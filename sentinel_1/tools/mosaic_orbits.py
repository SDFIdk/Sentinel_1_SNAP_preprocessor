from osgeo import gdal
import sys
import os
import numpy as np
import rasterio as rio
import rasterio.merge as merge
from rasterio.windows import Window
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

        # def mosaic_large_geotiffs(file_list, output_file):
        #     """
        #     Mosaic large GeoTIFF files by processing them in chunks.
        #     RUNS OUT OF MEMORY

        #     Parameters:
        #     - file_list (list): List of file paths to be merged.
        #     - output_file (str): Path to the output mosaic file.
        #     """

        #     band_names = band_names_from_metadata(file_list[0])
            
        #     files_to_mosaic = []
        #     for geotiff in file_list:
        #         src = rio.open(geotiff, 'r')
        #         files_to_mosaic.append(src)

        #     mosaic, out_trans = merge.merge(files_to_mosaic)

        #     out_meta = files_to_mosaic[0].meta.copy()
        #     out_meta.update({
        #         "driver": "GTiff",
        #         "height": mosaic.shape[1],
        #         "width": mosaic.shape[2],
        #         "transform": out_trans

        #     })

        #     with rio.open(output_file, 'w', **out_meta) as dst:
        #         dst.write(mosaic)
        #         for bidx, name in band_names:
        #             dst.set_band_description(bidx, name)

        #     for src in files_to_mosaic:
        #         src.close()

        def extract_datetime_from_filename(filename):
            """
            Extracts the datetime from the filename based on the specific pattern.
            
            Args:
            filename (str): The filename from which to extract the datetime.
            
            Returns:
            datetime: The extracted datetime object.
            """
            pattern = re.compile(r"S1A_IW_GRDH_1SDV_(\d{8}T\d{6})")
            S1A_IW_GRDH_1SDV_
            20240111T171839
            _20240111T171904_052062_064AC0_84B3.tif
            match = pattern.search(filename)
            if match:
                date_str = match.group(1)
                return datetime.strptime(date_str, '%Y%m%dT%H%M%S')
            else:
                raise ValueError(f"Filename {filename} does not match the expected pattern")

        def mosaic_large_geotiffs(file_list, output_file):

            band_names = band_names_from_metadata(file_list[0])
            print(band_names)
            print('---')
            print(file_list)


            src_ds_list = [gdal.Open(file) for file in file_list]
            print('---')
            print(src_ds_list)

            sys.exit()


            gdal.Warp(output_file, src_ds_list, format='GTiff', srcNodata=-9999, dstNodata=-9999)

            for ds in src_ds_list:
                ds = None


        mosaic_file_name = rename_output(mosaic_stack[0])  
        
        if len(mosaic_stack) == 1: 
            os.rename(mosaic_stack[0], mosaic_file_name)
        else:
            mosaic_large_geotiffs(mosaic_stack, mosaic_file_name)

        return mosaic_file_name

    def teardown(self):
        for geotiff in self.original_geotiffs: 
            Utils.safer_remove(geotiff)
