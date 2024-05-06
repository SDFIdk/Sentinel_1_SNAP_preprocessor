
from osgeo import gdal
import sys
from sentinel_1.tools.tif_tool import TifTool

gdal.UseExceptions()

class BuildPyramids(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads

    def printer(self):
        print(f"## Building pyramids...")

    def process_file(self, input_file):

        """
        Create pyramids for a GeoTIFF file using GDAL Python 
        bindings for ease of display in GIS software.
        """
        ds = gdal.Open(input_file, gdal.GA_Update)
        
        if ds is None:
            print("Failed to open file.")
            return
        
        ds.BuildOverviews("average", [2, 4, 8, 16, 32])
        ds = None