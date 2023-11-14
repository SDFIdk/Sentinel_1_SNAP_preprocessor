from osgeo import gdal
import sys
import os
from flood_utils import Utils

class Preprocessor(object):
    def __init__(self, input_dir, output_dir):
        if input_dir == None: input_dir = 'input/'
        self.input_dir = input_dir
        if output_dir == None: output_dir = 'output/'
        self.output_dir = output_dir
        self.geotiff_output_dir = output_dir + 'unfinished_geotiffs/'
        self.tmp = output_dir + 'tmp/'

        Utils.check_create_folder(self.input_dir)
        Utils.check_create_folder(self.tmp)
        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()


    def self_check(self, crs, polarization, denoise_mode):

        assert denoise_mode in ['SAR2SAR', 'mean'], f"## {denoise_mode} must match SAR2SAR or mean"   
        assert Utils.is_valid_epsg(crs.replace('EPSG:', '')), (
            '## CRS is not valid'
            )
        assert polarization != None, (
            '## Polarization cannot be none'
            '## Polarization must be either VV, VH, HV or HH'
            )
        if not isinstance(polarization, list):
            polarization = [polarization]
        for pol in polarization:
            assert pol in ['VV', 'VH', 'HV', 'HH'], (
                '## Polarization must be either VV, VH, HV or HH'
            )
        return


    def convert_to_geotiff(self, polarization):
        print('## Converting input files to geotiff...')
            
        os.makedirs(self.geotiff_output_dir, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(self.input_dir, '*.nc')
        for i, input_file in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.extract_polarization_band(self.geotiff_output_dir, input_file, polarization)
        return


    def warp_files_to_crs(self, crs):
        print('## Warping to CRS...')

        input_data_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        os.makedirs(self.tmp, exist_ok = True)
        
        for data in input_data_list:
            output_tif = self.tmp + os.path.basename(data)
            Utils.crs_warp(data, crs, output_tif)
        Utils.remove_folder(self.tmp)
        return
    

    def change_resolution(self, x_res, y_res):
        print('## Resampling resolution')
        os.makedirs(self.tmp, exist_ok = True)

        input_data_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        tmp_output = self.tmp + 'tmp.tif'
        for data in input_data_list:
            Utils.change_raster_resolution(data, tmp_output, x_res, y_res)
        return


    def sort_output(self, polarization, folder_name):
        print('## Sorting polarization and orbital direction')

        if not isinstance(polarization, list):
            polarization = [polarization]
        output = Utils.create_sorted_outputs(self.output_dir, polarization, folder_name)

        denoised_tifs = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        for i, tif in enumerate(denoised_tifs):
            print('# ' + str(i+1) + ' / ' + str(len(denoised_tifs)), end = '\r')
            Utils.sort_outputs(tif, polarization, output)


    def to_linear(self, zero_max = False):
        print('## Converting from linear to dB...')
        input_file_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        for i, db_geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')

            Utils.db_to_linear(db_geotiff, zero_max = zero_max)
        return


    def to_db(self):
        print('## Converting from dB to linear...')
        input_file_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        for i, lin_geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.linear_to_db(lin_geotiff)
        return


    def realign_rasters(self):
        print('## Fixing pixel alignment')
        input_file_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')

        _, reference_geotransform = Utils.get_references(input_file_list)

        os.makedirs(self.tmp, exist_ok = True)
        for i, raster_path in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.align_raster(raster_path, self.tmp + 'tmp.tif', reference_geotransform)
            