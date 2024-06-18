from osgeo import gdal
import os
import shutil
import sys
import tempfile
import uuid
from sentinel_1.tools.tif_tool import TifTool
from sentinel_1.utils import Utils

class AlignRaster(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.reference_geotransform = None
        self.threads = threads


    def setup(self):
        """
        Function prequisite for using align_raster
        Function returns the geotransform from the largest file in dir
        """

        input_file_list = Utils.file_list_from_dir(self.input_dir, "*.tif")
        reference_file = max(input_file_list, key=os.path.getsize)

        reference = gdal.Open(reference_file)
        reference_geotransform = reference.GetGeoTransform()
        reference = None

        self.reference_geotransform = reference_geotransform

    def printer(self):
        print("## Aligning rasters..")

    def process_file(self, input_file):
        """
        Ensures pixels in a raster are aligned to same grid.
        Requires "get_reference_geotransform" function to be run beforehand
        Takes reference_geotransform
        """

        path = os.path.split(input_file)[0]
        file_name = str(uuid.uuid4())[0:7] + '.tif'
        tmp_file_path = os.path.join(path, file_name)
        
        gdal.Warp(
            tmp_file_path,
            input_file,
            xRes=self.reference_geotransform[1],
            yRes=-self.reference_geotransform[5],
            targetAlignedPixels=True,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        shutil.move(tmp_file_path, input_file)

        return input_file
