from osgeo import gdal
import shutil
import sys
import uuid
from sentinel_1.tools.tif_tool import TifTool

gdal.UseExceptions()


class WarpCrs(TifTool):
    def __init__(self, input_dir, crs, threads = 1):
        self.input_dir = input_dir
        self.crs = crs
        self.threads = threads

    def printer(self):
        print(f"## Changing CRS..")

    def process_file(self, input_file):
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

        return input_file