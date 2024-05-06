import os
import shutil
import rio
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

        try:
            with rio.open(input_file) as src:
                # Copy the profile (metadata) from the source
                profile = src.profile
                
                # Update the profile to include compression
                profile.update(compress='lzw', predictor=2)  # 'lzw' compression with horizontal differencing

                # Write compressed data to a temporary file
                with rio.open(temp_path, 'w', **profile) as dst:
                    for i in range(1, src.count + 1):
                        data = src.read(i)
                        dst.write(data, i)
            
            # If successful, replace the original file with the compressed one
            os.close(temp_file)  # Close the file descriptor before replacing
            shutil.move(temp_path, input_file)
            print(f"Successfully compressed and replaced {input_file}")

        except Exception as e:
            os.close(temp_file)  # Ensure the file descriptor is closed on error
            os.remove(temp_path)  # Clean up the temporary file
            print(f"Failed to compress {input_file}: {e}")

