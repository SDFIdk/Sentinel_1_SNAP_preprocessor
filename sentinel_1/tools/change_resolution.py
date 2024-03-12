from osgeo import gdal
import shutil
import sys
import uuid
from sentinel_1.tools.tool import Tool


class ChangeResolution(Tool):
    def __init__(self, input_dir, resolution):
        self.input_dir = input_dir
        self.resolution = resolution

    def printer(self):
        print(f"## Changing resolution...")

    def loop(self, input_file):
        """
        Resamples a raster to a new resolution
        Takes x_size and y_size (defaults to square resolution if no y)
        """

        gdal_dataset = gdal.Open(input_file)

        output_file = str(uuid.uuid4()) + ".tif"

        warp_options = gdal.WarpOptions(
            xRes=self.resolution,
            yRes=self.resolution,
            resampleAlg="near",
            format="GTiff",
        )
        output_raster = gdal.Warp(output_file, gdal_dataset, options=warp_options)
        gdal_dataset = None
        output_raster = None

        shutil.move(output_file, input_file)
