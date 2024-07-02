from osgeo import gdal
import shutil
import os
import uuid

from sentinel_2.tools.s2_tools import S2TifTool

class ClipToShape(S2TifTool):

    def __init__(self, input_dir, shape, crs, threads = 1):
        self.input_dir = input_dir
        self.shape = shape
        self.crs = crs
        self.threads = threads

        gdal.UseExceptions()

    def printer():
        print("## Clipping geotiff to shape...")

    def process_file(self, input_file):

        options = gdal.WarpOptions(
            cutlineDSName=self.shape, cropToCutline=True, dstSRS=self.crs
        )

        tmp_output = os.path.basename(os.path.normpath(input_file)) + str(uuid.uuid4())

        gdal_dataset = gdal.Open(input_file)
        gdal.Warp(tmp_output, gdal_dataset, options=options)
        gdal_dataset = None
        shutil.move(input_file, tmp_output)