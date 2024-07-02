import zipfile
from osgeo import gdal
import os
import sys
import numpy as np
import rasterio as rio
from rasterio.mask import mask
from pathlib import Path
import glob
import shutil
import uuid
import pyproj
import geopandas as gpd
from shapely.geometry import mapping

gdal.UseExceptions()

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

    #OLD FILE, DIDNT HAVE WORKING SHAPE CUT
    # def aoi_cloud_cover(safe_file, shape):
    #     scl_filename = Utils.extract_scl(safe_file)

    #     scl_ds = rio.open(scl_filename).read(1)

    #     cloud_pixels = np.sum(np.isin(scl_ds, [8, 9]))
    #     # 8, 9 represents medium and high probability cloud classes in SRC
    #     total_data_pixels = scl_ds.size - np.sum(np.isin(scl_ds, [0]))

    #     scl_ds = None
    #     del scl_filename

    #     return (cloud_pixels / total_data_pixels) * 100


    def aoi_cloud_cover(safe_file, shape=None):
        scl_filename = Utils.extract_scl(safe_file)

        with rio.open(scl_filename) as scl_ds:
            scl_data = scl_ds.read(1)
            
            if shape:
                shapes = [mapping(geom) for geom in gpd.read_file(shape).geometry]
                scl_data, _ = mask(scl_ds, shapes, crop=True)
                scl_data = scl_data[0]

            cloud_pixels = np.sum(np.isin(scl_data, [8, 9])) #medium/high probability cloud classes in SCL
            total_data_pixels = scl_data.size - np.sum(np.isin(scl_data, [0]))

        os.remove(scl_filename)
        
        return (cloud_pixels / total_data_pixels) * 100


    def extract_scl(safe_file):
        with zipfile.ZipFile(safe_file, "r") as zip_ref:
            scl_file = [f for f in zip_ref.namelist() if "_SCL_20m.jp2" in f]

            scl_filename = "tmp/" + os.path.basename(scl_file[0])

            with zip_ref.open(scl_file[0]) as source, open(
                scl_filename, "wb"
            ) as target:
                target.write(source.read())
            return scl_filename

    def unzip_data_to_dir(data, output_dir, direct = False):
        if not direct:
            output_dir = output_dir + str(uuid.uuid4())
            Path(output_dir).mkdir(exist_ok=True)
        with zipfile.ZipFile(data, "r") as zip_ref:
            zip_ref.extractall(output_dir)

        if not direct:  return output_dir

    def remove_folder(folder):
        shutil.rmtree(folder)

    def get_immediate_subdirectories(a_dir):
        return [
            name
            for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))
        ]
