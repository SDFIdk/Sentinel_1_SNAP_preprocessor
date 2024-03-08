import zipfile
from osgeo import gdal, osr, ogr
import os
import sys
import geopandas as gpd
import numpy as np
from pathlib import Path
import glob
import shutil
import uuid
import pyproj
import tempfile
import rasterio as rio
from rasterio.windows import Window
from rasterio.enums import Compression
from rasterio.features import geometry_mask
import xml.etree.ElementTree as ET
import tifffile


class Utils(object):
    def __init__(self):
        self.test = "test"

    def gdal_error_handler(err_class, err_num, err_msg):
        errtype = {
            gdal.CE_None: "None",
            gdal.CE_Debug: "Debug",
            gdal.CE_Warning: "Warning",
            gdal.CE_Failure: "Failure",
            gdal.CE_Fatal: "Fatal",
        }
        err_msg = err_msg.replace("\n", " ")
        err_class = errtype.get(err_class, "None")
        print("Error Number: %s" % (err_num))
        print("Error Type: %s" % (err_class))
        print("Error Message: %s" % (err_msg))

    gdal.PushErrorHandler(gdal_error_handler)
    gdal.UseExceptions()

    def file_list_from_dir(directory, extensions, accept_no_files=False):
        """
        Returns file content of dir with given extension.
        If given a list of extensions, the function will whatever yields any files firt
        under assumption that the folder will only contain one type of files.
        """
        if not isinstance(extensions, list):
            extensions = [extensions]

        if not directory.endswith("/"):
            directory = directory + "/"

        for extension in extensions:
            if not extension.startswith("*"):
                extension = "*" + extension

            file_list = glob.glob(directory + extension)
            if file_list:
                break

        if not accept_no_files:
            assert len(file_list) != 0, f"## No {str(extensions)} files in {directory}!"
        return file_list

    def is_valid_epsg(epsg_code):
        """
        Checks whether provided EPSG code is valid
        """
        try:
            pyproj.CRS.from_epsg(epsg_code)
            return True
        except pyproj.exceptions.CRSError:
            return False

    def check_create_folder(directory):
        Path(directory).mkdir(exist_ok=True, parents=True)

    def remove_folder(folder):
        shutil.rmtree(folder)

    def shape_to_crs(shape, input_file, output_dir):
        gdf = gpd.read_file(shape)

        geotiff_crs = rio.open(input_file).crs

        gdf_warp = gdf.to_crs(geotiff_crs)

        new_shape_dir = os.path.join(output_dir, "crs_corrected_shape/")
        Path(new_shape_dir).mkdir(exist_ok=True)

        output_shape = new_shape_dir + "new_" + os.path.basename(shape)
        gdf_warp.to_file(output_shape)

        return output_shape

    # -----------------------------BELOW: MOVE TO SEPERATE FILES-----------------------------

    def unzip_data_to_dir(input_file, **kwargs):
        """
        Outputs content of zipfile to randomly named folder.
        Used for SAFE files
        """

        unzipped_safe = "tmp/" + str(uuid.uuid4()) + "/"
        Path(unzipped_safe).mkdir(exist_ok=True)
        with zipfile.ZipFile(input_file, "r") as zip_ref:
            zip_ref.extractall(unzipped_safe)

        return unzipped_safe


    def split_polarizations(input_file, **kwargs):
        """
        Splits a file with multiple polarization bands into one file per
        band with copies of auxiliary bands.
        Takes output_dir, polarization and crs
        """

        def get_orbital_direction(input_file, tag=65000):
            # 65000 is standard geotiff tag for metadata xml
            with tifffile.TiffFile(input_file) as tif:
                tree = tif.pages[0].tags[tag].value
                assert (
                    tree
                ), f"# {input_file} does not contain SNAP assocaited metadata!"

                root = ET.fromstring(tree)
                metadata = root.findall("Dataset_Sources")[0][0][0]

                for mdattr in metadata.findall("MDATTR"):
                    if not mdattr.get("name") == "PASS":
                        continue

                    orbital_direction = mdattr.text
                    if orbital_direction == "ASCENDING":
                        return "ASC"
                    elif orbital_direction == "DESCENDING":
                        return "DSC"

        def get_band_polarization(pol, data_bands):
            data_matches = []
            for i, band in enumerate(data_bands):
                if pol in band[1]:
                    data_matches.append((i + 1, pol))
            return data_matches

        def band_names_from_snap_geotiff(input_file, tag=65000):
            # 65000 is standard geotiff tag for metadata xml
            with tifffile.TiffFile(input_file) as tif:
                tree = tif.pages[0].tags[tag].value
                assert (
                    tree
                ), f"# {input_file} does not contain SNAP assocaited metadata!"

                root = ET.fromstring(tree)
                data_access = root.findall("Data_Access")[0]

                data_bands = []
                incidence_bands = []
                for i, data_file in enumerate(data_access.findall("Data_File")):
                    band_name = data_file.find("DATA_FILE_PATH").get("href")
                    band_name = os.path.splitext(os.path.basename(band_name))[0]

                    if "VV" in band_name or "VH" in band_name:
                        data_bands.append((i + 1, band_name))
                    else:
                        incidence_bands.append((i + 1, band_name))

            return data_bands, incidence_bands, root

        output_dir = kwargs.get("output_dir")
        polarization = kwargs.get("polarization")
        shape = kwargs.get("shape")

        data_bands, incidence_bands, metadata_xml = band_names_from_snap_geotiff(
            input_file
        )
        orbit_direction = get_orbital_direction(input_file)

        #Clipping file down here saves a lot of compute
        from sentinel_1.utils import Utils
        Utils.clip_256(input_file, **kwargs)

        with rio.open(input_file) as src:
            meta = src.meta.copy()
            meta.update(
                count=src.count - (len(polarization) - 1), compress=Compression.lzw.name
            )

            selected_data_bands = [
                item
                for pol in polarization
                for item in get_band_polarization(pol, data_bands)
            ]

            for i, (data_index, data_band) in enumerate(selected_data_bands, start=1):
                band_info = data_band + "_" + orbit_direction
                filename = (
                    os.path.basename(input_file).replace(Path(input_file).suffix, "_")
                    + band_info
                    + "_band.tif"
                )
                output_geotiff = os.path.join(output_dir, filename)

                with rio.open(output_geotiff, "w", **meta) as dst:
                    dst.write(src.read(data_index), 1)
                    dst.set_band_description(1, data_band)
                    dst.update_tags(ns="xml", **{"TIFFTAG_XMLPACKET": metadata_xml})
                    dst.nodata = -9999

                    for i, (incidence_index, incidence_band) in enumerate(
                        incidence_bands, start=2
                    ):
                        dst.write(src.read(incidence_index), i)
                        dst.set_band_description(i, incidence_band)

        os.remove(input_file)

    def get_reference_geotransform(**kwargs):
        """
        Function prequisite for using align_raster
        Function returns the geotransform from the largest file in dir
        """
        input_dir = kwargs.get("input_dir")

        input_file_list = Utils.file_list_from_dir(input_dir, "*.tif")
        reference_file = max(input_file_list, key=os.path.getsize)

        reference = gdal.Open(reference_file)
        reference_geotransform = reference.GetGeoTransform()
        reference = None

        arg_name = "reference_geotransform"
        kwargs[arg_name] = reference_geotransform

        return kwargs

    def clip_256(input_file, **kwargs):
        """
        Clips a geotiff to a rasters extent, padded to output a resolution divisible by 256
        Takes shape, crs and input_dir
        """
        shape = kwargs.get("shape")
        crs = kwargs.get("crs")
        input_dir = kwargs.get("input_dir")

        shape = Utils.shape_to_crs(shape, input_file, input_dir)

        ds = ogr.Open(shape)
        layer = ds.GetLayer()
        extent = layer.GetExtent()
        minX, maxX, minY, maxY = extent

        maxX = maxX + 2560
        maxY = maxY + 2560
        nodata_value = -9999

        src = gdal.Open(input_file, gdal.GA_ReadOnly)
        src_srs = src.GetProjection()

        warp_options = gdal.WarpOptions(
            outputBounds=[minX, minY, maxX, maxY],
            cutlineDSName=shape,
            cropToCutline=True,
            dstNodata=nodata_value,
            srcSRS=src_srs,
            dstSRS=crs,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
            tmp_file_path = tmp_file.name

        _ = gdal.Warp(tmp_file_path, src, options=warp_options)

        ds = None
        src = None

        with rio.open(tmp_file_path) as src:
            new_width = (src.width // 256) * 256
            new_height = (src.height // 256) * 256

            window = Window(0, 0, new_width, new_height)
            clipped_data = src.read(window=window)
            new_transform = src.window_transform(window)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
                tmp_file_path_2 = tmp_file.name

            with rio.open(
                tmp_file_path_2,
                "w",
                driver="GTiff",
                height=new_height,
                width=new_width,
                count=src.count,
                dtype=str(clipped_data.dtype),
                crs=crs,
                nodata=-9999,
                transform=new_transform,
            ) as dst:
                dst.write(clipped_data)

        shutil.move(tmp_file_path_2, input_file)


gdal.UseExceptions()
