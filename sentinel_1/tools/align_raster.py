from osgeo import gdal
import os
import shutil
import sys
import tempfile
from sentinel_1.tools.tool import Tool
from sentinel_1.utils import Utils


class AlignRaster(Tool):
    def __init__(self, input_dir):
        self.input_dir = input_dir
        self.reference_geotransform = None

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

    def loop(self, input_file):
        """
        Ensures pixels in a raster are aligned to same grid.
        Requires "get_reference_geotransform" function to be run beforehand
        Takes reference_geotransform
        """

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
            tmp_file_path = tmp_file.name  # Get the temporary file path

        gdal.Warp(
            tmp_file_path,
            input_file,
            xRes=self.reference_geotransform[1],
            yRes=-self.reference_geotransform[5],
            targetAlignedPixels=True,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        shutil.move(tmp_file_path, input_file)
