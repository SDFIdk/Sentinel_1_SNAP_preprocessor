from osgeo import gdal
import sys
import os
import multiprocessing

from sentinel_2.s2_utils import Utils
from sentinel_2.tiff_generator import Tiff_generator


class Preprocessor(object):
    def __init__(self, input_dir, output_dir):
        if input_dir == None:
            input_dir = "input/"
        self.input_dir = input_dir
        if output_dir == None:
            output_dir = "output/"
        self.output_dir = output_dir
        # self.output_dir = output_dir + 'unprocessed_geotiffs/'
        self.tmp = "tmp/"

        Utils.check_create_folder(self.input_dir)
        Utils.check_create_folder(self.output_dir)

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

    def self_check(self, crs):
        assert Utils.is_valid_epsg(crs.replace("EPSG:", "")), "## CRS is not valid"
        return

    def s2_safe_to_geotiff(self, max_cloud, shape=None):
        print("## Converting SAFE to geotiff...")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.tmp, exist_ok=True)

        safe_file_list = Utils.file_list_from_dir(self.input_dir, "*.zip")
        for i, safe_file in enumerate(safe_file_list):
            print("# " + str(i + 1) + " / " + str(len(safe_file_list)), end="\r")

            cloud_clover_in_aoi = Utils.aoi_cloud_cover(safe_file, shape)

            if cloud_clover_in_aoi > max_cloud or None:
                print("# skipping clouds...")
                continue

            Tiff_generator.generate_geotiffs(safe_file, self.output_dir)
        return

    def warp_files_to_crs(self, crs):
        print("## Warping to CRS...")

        input_data_list = Utils.file_list_from_dir(self.output_dir, "*.tif")
        os.makedirs(self.tmp, exist_ok=True)

        for i, data in enumerate(input_data_list):
            print("# " + str(i + 1) + " / " + str(len(input_data_list)), end="\r")

            output_tif = self.tmp + os.path.basename(data)
            Utils.crs_warp(data, crs, output_tif)
        Utils.remove_folder(self.tmp)
        return

    def clip_to_shape(self, shape, crs):
        print("## Clipping geotiff to shape...")

        if shape == None:
            return

        output_tif = self.tmp + "tmp.tif"
        os.makedirs(self.tmp, exist_ok=True)

        input_data_list = Utils.file_list_from_dir(self.output_dir, "*.tif")
        for i, data in enumerate(input_data_list):
            print("# " + str(i + 1) + " / " + str(len(input_data_list)), end="\r")

            data = data.replace("\\", "/")

            options = gdal.WarpOptions(
                cutlineDSName=shape, cropToCutline=True, dstSRS=crs
            )
            Utils.open_option_warp_move(data, options, output_tif)

        del output_tif

    def remove_empty_files(self, max_empty_percent=50):
        print("## Removing images with too little data...")
        input_data_list = Utils.file_list_from_dir(self.output_dir, "*.tif")
        for i, data in enumerate(input_data_list):
            print("# " + str(i + 1) + " / " + str(len(input_data_list)), end="\r")

            Utils.remove_empty_files(data, max_empty_percent)
