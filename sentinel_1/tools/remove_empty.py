import rasterio as rio
import numpy as np
import sys
import os

from sentinel_1.tools.tif_tool import TifTool


class RemoveEmpty(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads


    def printer(self):
        print(f"## Removing empty rasters...")

    def process_file(self, input_file):
        """
        Finds geotiffs with no data and deletes them. Outputs none
        Used for geotiffs
        """
        with rio.open(input_file) as src:
            data = src.read(1)

            if not np.all(np.isnan(data)):
                return input_file

            os.remove(input_file)
            return None