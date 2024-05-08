import os
import shutil
import rasterio as rio
from rasterio.enums import Compression
import tempfile
import sys

from sentinel_1.tools.tif_tool import TifTool

class GeotiffCompressor(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads

    def printer(self):
        print(f"## Compressing geotiffs...")

    def process_file(self, input_file):
        """
        Compresses geotiffs
        """
        temp_file, temp_path = tempfile.mkstemp(suffix='.tif')

        with rio.open(input_file) as src:
            profile = src.profile
            
            profile.update(compress='lzw', predictor=2)  # 'lzw' compression with horizontal differencing

            with rio.open(temp_path, 'w', **profile) as dst:
                for i in range(1, src.count + 1):
                    data = src.read(i)
                    dst.write(data, i)
        
        os.close(temp_file)
        shutil.move(temp_path, input_file)

        return input_file
