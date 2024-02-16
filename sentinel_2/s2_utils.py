import zipfile
from osgeo import gdal
import os
import sys
import numpy as np
import rasterio as rio
from pathlib import Path
import glob
import shutil
import uuid
import pyproj


class Utils(object):
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
        try:
            pyproj.CRS.from_epsg(epsg_code)
            return True
        except pyproj.exceptions.CRSError:
            return False

    def check_create_folder(directory):
        Path(directory).mkdir(exist_ok=True)

    def aoi_cloud_cover(safe_file, shape):
        scl_filename = Utils.extract_scl(safe_file)

        if shape:
            options = gdal.WarpOptions(
                cutlineDSName=shape, cropToCutline=True, dstSRS="EPSG:4326"
            )
            Utils.open_option_warp_move(scl_filename, options, "tmp/clip_scl.jp2")

        cloud_percentage = Utils.get_cloud_percentage(scl_filename)
        del scl_filename
        return cloud_percentage

    def get_cloud_percentage(scl_filename):
        scl_ds = rio.open(scl_filename).read(1)

        cloud_pixels = np.sum(np.isin(scl_ds, [8, 9]))
        # 8, 9 represents medium and high probability cloud classes in SRC
        total_data_pixels = scl_ds.size - np.sum(np.isin(scl_ds, [0]))

        scl_ds = None
        return (cloud_pixels / total_data_pixels) * 100

    def extract_scl(safe_file):
        with zipfile.ZipFile(safe_file, "r") as zip_ref:
            scl_file = [f for f in zip_ref.namelist() if "_SCL_20m.jp2" in f]

            assert (
                scl_file
            ), f"## SCL cloud layer not found in {os.path.basename(safe_file)} !"

            scl_filename = "tmp/" + os.path.basename(scl_file[0])

            with zip_ref.open(scl_file[0]) as source, open(
                scl_filename, "wb"
            ) as target:
                target.write(source.read())
            return scl_filename

    def unzip_data_to_dir(data, tmp):
        unzipped_safe = tmp + str(uuid.uuid4())
        Path(unzipped_safe).mkdir(exist_ok=True)
        with zipfile.ZipFile(data, "r") as zip_ref:
            zip_ref.extractall(unzipped_safe)

        return unzipped_safe

    def remove_folder(folder):
        shutil.rmtree(folder)

    def crs_warp(dataset, crs, output):
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)

        options = gdal.WarpOptions(
            format="GTiff",
            srcSRS=gdal_dataset.GetProjection(),
            dstSRS=crs,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        gdal.Warp(output, gdal_dataset, options=options)
        shutil.move(output, dataset)

    def open_option_warp_move(dataset, options, output):
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)
        gdal.Warp(output, gdal_dataset, options=options)
        shutil.move(output, dataset)

    def remove_empty_files(geotiff, max_empty_percent):
        with rio.open(geotiff, "r") as src:
            zero_pixel_count = (src.read(1) == 0).sum()
            total_pixels = src.read(1).size
            percentage = (zero_pixel_count / total_pixels) * 100

        if percentage >= max_empty_percent:
            print(f"# Removed {geotiff}, data coverage: {str(100 - percentage)} %")
            os.remove(geotiff)

    def move_data(source, destination, copy=False):
        if copy:
            shutil.copy(source, destination)
        else:
            shutil.move(source, destination)
