import zipfile
from osgeo import gdal, ogr
import os
import sys
import geopandas as gpd
from pathlib import Path
import glob
import shutil
import uuid
import pyproj
import tempfile
import rasterio as rio
from rasterio.windows import Window
import time


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
        if not os.path.isdir(directory):
            return [directory]

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

    def shape_to_crs(shape, output_shape, crs_geotiff = False, target_crs = False):
        gdf = gpd.read_file(shape)

        assert (crs_geotiff != target_crs), (
            "Only provide either crs_geotiff or target_crs!"
        )

        if crs_geotiff: target_crs = rio.open(crs_geotiff).crs

        gdf_warp = gdf.to_crs(target_crs)

        new_shape_dir = os.path.join(output_shape, "crs_corrected_shape/")
        Path(new_shape_dir).mkdir(exist_ok=True, parents=True)

        output_shape = new_shape_dir + "new_" + os.path.basename(shape)
        gdf_warp.to_file(output_shape)

        return output_shape
    
    def safer_remove(path):
        """Attempt to remove a file or directory with retries for locked files."""
        max_retries = 5
        retry_delay = 1  # one second

        for _ in range(max_retries):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
                break
            except Exception as e:
                print(f"# Warning: failed to delete {path} due to {e}")
                time.sleep(retry_delay)
        else:
            print(f"# Error: could not delete {path} after {max_retries} retries.")

    def clip_256_single(input_file, shape, crs):
        """
        Clips a geotiff to a rasters extent, padded to output a resolution divisible by 256
        Takes shape, crs and input_dir
        """
        crs_corrected_shape = Utils.shape_to_crs(
            shape, output_shape=os.path.dirname(input_file), crs_geotiff=input_file
        )
        ds = ogr.Open(crs_corrected_shape)
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
            cutlineDSName=crs_corrected_shape,
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

            #OLD METHOD, RAM INTENSIVE
            # with rio.open(
            #     tmp_file_path_2,
            #     "w",
            #     driver="GTiff",
            #     height=new_height,
            #     width=new_width,
            #     count=src.count,
            #     dtype=str(clipped_data.dtype),
            #     crs=crs,
            #     nodata=-9999,
            #     transform=new_transform,
            # ) as dst:
            #     dst.write(clipped_data)

            with rio.open(
                tmp_file_path_2,
                "w",
                driver="GTiff",
                height=new_height,
                width=new_width,
                count=src.count,
                dtype=src.dtypes[0],
                crs=crs,
                nodata=-9999,
                transform=new_transform
            ) as dst:
                for j, window in src.block_windows(1):
                    data = src.read(window=window)
                    new_transform = src.window_transform(window)
                    dst.write(data, window=window)
                    dst.set_transform(new_transform, window=window)

        shutil.move(tmp_file_path_2, input_file)

        Utils.safer_remove(crs_corrected_shape)

    def extract_from_metadata(input_file, tag):
        with rio.open(input_file, 'r') as src:
            metadata = src.tags()[tag]
        return metadata


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
