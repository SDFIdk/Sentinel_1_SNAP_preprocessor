import os
from osgeo import gdal
import uuid
import shutil

from sentinel_2.tools.s2_tools import S2TifTool

class CRSWarp(S2TifTool):
    def __init__(self, input_dir, crs, threads = 1):
        self.input_dir = input_dir
        self.crs = crs
        self.threads = threads

        gdal.UseExceptions()


    def printer():
        print("## Warping to CRS...")

    def process_file(self, input_file):

        tmp_output = os.path.basename(os.path.normpath(input_file)) + str(uuid.uuid4())

        gdal_dataset = gdal.Open(input_file)

        options = gdal.WarpOptions(
            format="GTiff",
            srcSRS=gdal_dataset.GetProjection(),
            dstSRS=self.crs,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        gdal.Warp(tmp_output, gdal_dataset, options=options)

        shutil.move(tmp_output, input_file)
