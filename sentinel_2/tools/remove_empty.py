import os
import rasterio as rio

from sentinel_2.tools.s2_tools import S2TifTool

class RemoveEmpty(S2TifTool):

    def __init__(self, input_dir, max_empty, threads = 1):
        self.input_dir = input_dir
        self.max_empty = max_empty

    def printer():
        print("## Removing images with too little data...")

    def process_file(self, input_file):

        with rio.open(input_file, "r") as src:
            zero_pixel_count = (src.read(1) == 0).sum()
            total_pixels = src.read(1).size
            percentage = (zero_pixel_count / total_pixels) * 100

        if percentage >= self.max_empty:
            print(f"# Removed {input_file}, data coverage: {str(100 - percentage)} %")
            os.remove(input_file)