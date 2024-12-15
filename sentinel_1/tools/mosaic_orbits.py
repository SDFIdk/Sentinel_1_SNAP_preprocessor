from osgeo import gdal
import sys
import os
from datetime import datetime
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
        
        # def band_names_from_metadata(input_file):

        #     data_bands = ast.literal_eval(Utils.extract_from_metadata(input_file, 'data_bands'))
        #     incidence_bands = ast.literal_eval(Utils.extract_from_metadata(input_file, 'incidence_bands'))
            
        #     return data_bands + incidence_bands

        def datetime_from_s1_filename(geotiff):
            """
            Extracts the datetime from Sentinel-1 GRD filename patterns
            
            Args:
            filename (str): The filename from which to extract the datetime.
            
            Returns:
            datetime: The extracted datetime object.
            """
            date_str = os.path.basename(geotiff)[17:32]
            return datetime.strptime(date_str, '%Y%m%dT%H%M%S')


        def mosaic_large_geotiffs(file_list, output_file):

            # band_names = band_names_from_metadata(file_list[0])

            src_ds_list = [gdal.Open(file) for file in file_list]

            num_bands = src_ds_list[0].RasterCount

            gdal.Warp(output_file, 
                      src_ds_list, 
                      format='GTiff', 
                      srcNodata=0,
                      dstNodata=-9999,
                      options=['COMPRESS=LZW', 'TILED=YES']
                      )
            
            out_ds = gdal.Open(output_file, gdal.GA_Update)
            for band_idx in range(1, num_bands + 1):
                band_name = src_ds_list[0].GetRasterBand(band_idx).GetDescription()
                out_ds.GetRasterBand(band_idx).SetDescription(band_name)


        mosaic_file_name = rename_output(mosaic_stack[0])  
        
        if len(mosaic_stack) == 1: 
            os.rename(mosaic_stack[0], mosaic_file_name)
        else:
            mosaic_stack.sort(key=lambda x: datetime_from_s1_filename(os.path.basename(x)), reverse=True)
            mosaic_large_geotiffs(mosaic_stack, mosaic_file_name)

        return mosaic_file_name

    def teardown(self):
        for geotiff in self.original_geotiffs: 
            Utils.safer_remove(geotiff)