from osgeo import gdal
import sys
import os
from flood_utils import Utils
from sar2sar_main import SAR2SAR

class Preprocessor(object):
    def __init__(self, input_dir, output_dir):
        if input_dir == None: input_dir = 'input/'
        self.input_dir = input_dir
        if output_dir == None: output_dir = 'output/'
        self.output_dir = output_dir
        self.geotiff_output_dir = output_dir + 'unfinished_geotiffs/'
        self.tmp = output_dir + 'tmp/'
        self.denoised_geotiffs = output_dir + 'denoised_geotiffs/'
        self.checkpoint = 'checkpoint/'
        self.orbit_dir = 'orbit/'

        Utils.check_create_folder(self.input_dir)
        Utils.check_create_folder(self.tmp)

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()


    def self_check(self, crs, polarization, unit, denoise_mode):
    
        if not unit in ['decibel', 'linear']:
            print('## Unit must be either linear or decibel')
            sys.exit()

        if not Utils.is_valid_epsg(crs.replace('EPSG:', '')):
            print('## CRS is not valid')
            sys.exit()

        if polarization == None:
            print('## Polarization cannot be none')
            print('## Polarization must be either VV, VH, HV or HH')
            sys.exit()
        if not isinstance(polarization, list):
            polarization = [polarization]
        for pol in polarization:
            if not pol in ['VV', 'VH', 'HV', 'HH']:
                print('## Polarization must be either VV, VH, HV or HH')
                sys.exit()
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


    def clip_to_256(self, shape, crs):
        print('## Clipping files to shape...')

        geotiff_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        os.makedirs(self.tmp, exist_ok = True)

        shape = Utils.shape_to_crs(shape, crs, self.output_dir)

        for i, geotiff in enumerate(geotiff_list):
            print('# ' + str(i+1) + ' / ' + str(len(geotiff_list)), end = '\r')

            Utils.clip_to_256(geotiff, shape, self.tmp, crs)

        return 


    def denoise(self, denoise_mode):

        # tmp_denoise_output = self.tmp
        noisy_npy_folder = self.tmp + 'npy_files/'
        denoised_npy_folder = self.tmp + 'denoised_numpys/'
        os.makedirs(noisy_npy_folder, exist_ok = True)
        os.makedirs(denoised_npy_folder, exist_ok = True)

        if denoise_mode == 'SAR2SAR':
            print('## SAR2SAR mode selected')

            noisy_npy_folder = Utils.convert_to_npy(self.geotiff_output_dir, noisy_npy_folder)
            SAR2SAR.SAR2SAR_main(noisy_npy_folder, denoised_npy_folder, self.checkpoint)

            Utils.remove_folder(noisy_npy_folder)
        else:
            print('## Mean filter mode selected')
            denoised_npy_folder = Utils.apply_mean_filter(self.geotiff_output_dir, denoised_npy_folder)

        Utils.recreate_geotiff(denoised_npy_folder, self.geotiff_output_dir, self.tmp)

        Utils.remove_folder(self.tmp)

    
    def sort_output(self, polarization):
        print('## Sorting polarization and orbital direction')

        if not isinstance(polarization, list):
            polarization = [polarization]

        output = Utils.create_sorted_outputs(self.tmp, polarization)

        denoised_tifs = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        for i, tif in enumerate(denoised_tifs):
            print('# ' + str(i+1) + ' / ' + str(len(denoised_tifs)), end = '\r')
            Utils.sort_outputs(tif, polarization, output)


    def to_linear(self):
        print('## Converting from linear to dB...')
        input_file_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        for i, db_geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')

            Utils.db_to_linear(db_geotiff)
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

        reference_projection, reference_geotransform = Utils.get_references(input_file_list)

        os.makedirs(self.tmp, exist_ok = True)
        for i, raster_path in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')

            output_path = self.tmp + 'tmp.tif'

            Utils.align_raster(raster_path, output_path, reference_projection, reference_geotransform)
            