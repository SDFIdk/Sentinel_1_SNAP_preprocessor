import rasterio as rio
import numpy as np
import sys
import os

from sentinel_1.tools.tool import Tool


class RemoveEmpty(Tool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads


    def printer(self):
        print(f"## Removing empty rasters...")

    def loop(self, input_file):
        """
        Finds geotiffs with no data and deletes them. Outputs none
        Used for geotiffs
        """
        with rio.open(input_file) as src:
            data = src.read(1)

            if not np.all(np.isnan(data)):
                return

            os.remove(input_file)
