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

    def remove_empty(input_file, **kwargs):
        """
        Finds geotiffs with no data and deletes them. Outputs none
        Used for geotiffs
        """
        with rio.open(input_file) as src:
            data = src.read(1)

            if not np.all(np.isnan(data)):
                return

            os.remove(input_file)
        return

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

    def crs_warp(input_file, **kwargs):
        """
        Warps a raster to a new crs
        Takes crs
        """
        crs = kwargs.get("crs")
        gdal_dataset = gdal.Open(input_file)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        output_file = str(uuid.uuid4()) + ".tif"

        options = gdal.WarpOptions(
            format="GTiff",
            dstSRS=crs,
            xRes=x_res,
            yRes=y_res,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )
        gdal.Warp(output_file, gdal_dataset, options=options)
        shutil.move(output_file, input_file)

    def change_raster_resolution(input_file, **kwargs):
        """
        Resamples a raster to a new resolution
        Takes x_size and y_size (defaults to square resolution if no y)
        """
        x_size = kwargs.get("x_size")
        y_size = kwargs.get("y_size", x_size)

        gdal_dataset = gdal.Open(input_file)

        output_file = str(uuid.uuid4()) + ".tif"

        warp_options = gdal.WarpOptions(
            xRes=x_size, yRes=y_size, resampleAlg="near", format="GTiff"
        )
        output_raster = gdal.Warp(output_file, gdal_dataset, options=warp_options)
        gdal_dataset = None
        output_raster = None

        shutil.move(output_file, input_file)

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

    def sort_output(input_file, **kwargs):
        """
        Sorts geotiffs into folder based on polarizaton and orbital direction
        Requires "create_sorted_outputs" function to be run beforehand
        Takes output_sub_dir and polarization
        """
        result_dir = kwargs.get("result_dir")
        polarization = kwargs.get("polarization")
        denoise_mode = kwargs.get("denoise_mode")
        unit = kwargs.get("unit")
        resolution = kwargs.get("resolution")

        if not isinstance(polarization, list):
            polarization = [polarization]

        file_polarization = None
        for pol in polarization:
            if pol in input_file:
                file_polarization = pol

        product_dir = denoise_mode + "_" + str(resolution) + "m_" + unit

        sort_dir = os.path.join(result_dir, product_dir, file_polarization)
        Utils.check_create_folder(sort_dir)
        sort_filename = os.path.join(sort_dir, os.path.basename(input_file))
        shutil.copyfile(input_file, sort_filename)
        return

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

    def align_raster(input_file, **kwargs):
        """
        Ensures pixels in a raster are aligned to same grid.
        Requires "get_reference_geotransform" function to be run beforehand
        Takes reference_geotransform
        """
        reference_geotransform = kwargs.get("reference_geotransform")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
            tmp_file_path = tmp_file.name

        gdal.Warp(
            tmp_file_path,
            input_file,
            xRes=reference_geotransform[1],
            yRes=-reference_geotransform[5],
            targetAlignedPixels=True,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        shutil.move(tmp_file_path, input_file)
        return

    def copy_dir(input_file, **kwargs):
        """
        Creates a copy of the directory given to it to a given location
        Takes file and copy_dir
        """
        copy_dir = kwargs.get("copy_dir")

        Utils.check_create_folder(copy_dir)

        copy_file = copy_dir + os.path.basename(input_file)
        shutil.copyfile(input_file, copy_file)

    def trimmer_256(input_file, **kwargs):
        """
        Trims a dataset to a resolution divisible by 256
        """

        dataset = gdal.Open(input_file)

        original_width = dataset.RasterXSize
        original_height = dataset.RasterYSize

        new_width = (original_width // 256) * 256
        new_height = (original_height // 256) * 256

        if new_width == original_width and new_height == original_height:
            return
        else:
            temp_output_path = "tmp.tif"
            driver = gdal.GetDriverByName("GTiff")
            out_dataset = driver.Create(
                temp_output_path,
                new_width,
                new_height,
                dataset.RasterCount,
                dataset.GetRasterBand(1).DataType,
            )
            out_dataset.SetGeoTransform(dataset.GetGeoTransform())
            out_dataset.SetProjection(dataset.GetProjection())

            for i in range(dataset.RasterCount):
                in_band = dataset.GetRasterBand(i + 1)
                out_band = out_dataset.GetRasterBand(i + 1)

                data = in_band.ReadAsArray(0, 0, new_width, new_height)
                out_band.WriteArray(data)
        dataset = None
        out_dataset = None
        out_band = None

        shutil.move(temp_output_path, input_file)

    def convert_unit(input_file, **kwargs):
        """
        Converts units from raw backscatter to decibel or "power transform".
        True zero_max will cap values of non linear at zero.
        Takes source_unit, desitnation_unit and zero_max
        """
        source_unit = kwargs.get("source_unit")
        destination_unit = kwargs.get("destination_unit")
        try:
            zero_max = kwargs.get("zero_max")
        except:
            zero_max = False

        def only_zero_max_conversion(geotiff):
            with rio.open(geotiff, "r+") as src:
                dataset = src.read(1)
                zero_max_func(dataset)
                src.write(dataset, 1)
            return

        def zero_max_func(dataset):
            dataset[dataset > 0] = 0
            return dataset

        def no_op(geotiff, zero_max=False):
            return geotiff

        def generic_transform(dataset_in, equation, zero_max=False):
            dataset_out = equation(dataset_in)
            if zero_max:
                dataset_out = zero_max_func(dataset_out)
            return dataset_out

        source_to_linear = {
            "decibel": lambda a: 10.0 ** (a / 10.0),
            "power": lambda a: a**10,
            "linear": no_op,
        }
        linear_to_dest = {
            "decibel": lambda a: 10.0 * np.log10(a),
            "power": lambda a: a**0.1,
            "linear": no_op,
        }

        np.seterr(divide="ignore")

        if source_unit == destination_unit and zero_max:
            assert source_unit != "linear", "## Cannot set linear values to zero!"
            only_zero_max_conversion(input_file)
            return

        zero_max_out = False
        if zero_max and source_unit == "linear":
            zero_max_out = True
        zero_max_in = False
        if zero_max and destination_unit == "linear":
            zero_max_in = True

        with rio.open(input_file, "r+") as src:
            dataset = src.read(1)
            dataset = generic_transform(
                dataset, source_to_linear[source_unit], zero_max_in
            )
            dataset = generic_transform(
                dataset, linear_to_dest[destination_unit], zero_max_out
            )
            src.write(dataset, 1)

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

    def land_sea_mask(input_file, **kwargs):
        """
        Sets all values in a raster outside a polygon to noData
        Default set to the Danish Landpolygon
        Takes land_sea_mask, input_dir
        """
        land_sea_mask = kwargs.get("land_sea_mask")
        input_dir = kwargs.get("input_dir")

        shape = gpd.read_file(land_sea_mask)
        
        with rio.open(input_file) as src:
            mask = geometry_mask([geometry for geometry in shape.geometry], 
                                transform=src.transform, 
                                invert=True, 
                                out_shape=(src.height, src.width))
            
            raster_data = src.read(1)  #only necessary to read the data band which is always first
            
            raster_data[~mask] = -9999
            
            new_meta = src.meta.copy()
            new_meta['nodata'] = -9999
            
            tmp_geotiff = os.path.join(input_dir, "tmp.tif")
            with rio.open(tmp_geotiff, 'w', **new_meta) as dst:
                dst.write(raster_data, 1)
        shutil.move(tmp_geotiff, input_file)

    # def TEST_FUNK(input_file, **kwargs):
    #     """
    #     TEST FUNCTION
    #     Takes test_var
    #     """
    #     test_var = kwargs['test_var']

    #     print(input_file)
    #     print(kwargs)
    #     print('------')

    #     # for arg in kwargs:
    #     #     print(arg)
    #     for k, v in kwargs.items():
    #         print("%s = %s" % (k, v))

    #     sys.exit()


gdal.UseExceptions()
