from osgeo import gdal
import sys
import os
import rasterio as rio
import xml.etree.ElementTree as ET
import glob
import ast
from sentinel_1.tools.tif_tool import TifTool
from sentinel_1.utils import Utils

gdal.UseExceptions()

class MosaicOrbits(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads

    def printer(self):
        print(f"## Mosaicing files with common orbits..")

    def files(self):
        #MosaicOrbits handles its own file collecting as it deals with lists of geotiffs
        self.original_geotiffs = glob.glob(self.input_dir + '/*.tif')

        orbit_dict = {}
        for geotiff in glob.glob(self.input_dir + '/*.tif'):
            geotiff_name = os.path.basename(geotiff)
            
            key = geotiff_name[49:55]

            if key in orbit_dict:
                orbit_dict[key].append(geotiff)
            else:
                orbit_dict[key] = [geotiff]

        return [*orbit_dict.values()]
        

    def process_file(self, mosaic_stack):
        """
        Combines images from the same orbit on within the same day into a single image
        """

        def rename_output(output_file):
            return os.path.splitext(output_file)[0] + '_ORBIT_MOSAIC' + os.path.splitext(output_file)[1]
        
        def band_names_from_metadata(input_file):

            data_bands = ast.literal_eval(Utils.extract_from_metadata(input_file, 'data_bands'))
            incidence_bands = ast.literal_eval(Utils.extract_from_metadata(input_file, 'incidence_bands'))
            
            return data_bands + incidence_bands

        def mosaic_large_geotiffs(file_list, output_file):
            """
            Mosaic large GeoTIFF files by processing them in chunks.

            Parameters:
            - file_list (list): List of file paths to be merged.
            - output_file (str): Path to the output mosaic file.
            """

            band_names = band_names_from_metadata(file_list[0])
            
            with rio.open(file_list[0]) as src:
                meta = src.meta.copy()

            with rio.open(output_file, 'w', **meta) as dst:
                for file in file_list:
                    with rio.open(file) as src:

                        for _, window in src.block_windows(1):
                            data = src.read(window=window)
                            dst.write(data, window=window)

                    print(f"# Processed and added {file} to mosaic.")

                for bidx, name in band_names:
                    dst.set_band_description(bidx, name)

                dst.no_data = -9999


        mosaic_file_name = rename_output(mosaic_stack[0])  
        
        if len(mosaic_stack) == 1: 
            os.rename(mosaic_stack[0], mosaic_file_name)
        else:
            mosaic_large_geotiffs(mosaic_stack, mosaic_file_name)

        return mosaic_file_name


    def teardown(self):
        for geotiff in self.original_geotiffs: 
            Utils.safer_remove(geotiff)
