from osgeo import gdal
import shutil
import sys
import uuid
from sentinel_1.tools.tool import Tool

gdal.UseExceptions()

class WarpCrs(Tool):
    def __init__(self, input_dir, crs):
        self.input_dir = input_dir
        self.crs = crs

    def loop(self, input_file):
        """
        Warps a raster to a new crs
        Takes crs
        """
        gdal_dataset = gdal.Open(input_file)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        output_file = str(uuid.uuid4()) + ".tif"

        options = gdal.WarpOptions(
            format="GTiff",
            dstSRS=self.crs,
            xRes=x_res,
            yRes=y_res,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )
        gdal.Warp(output_file, gdal_dataset, options=options)
        shutil.move(output_file, input_file)
