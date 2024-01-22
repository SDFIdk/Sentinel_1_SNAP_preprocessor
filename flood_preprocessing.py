from osgeo import gdal
import sys
import os
from flood_utils import Utils
from multiprocessing.pool import Pool
from flood_utils_ditest import TEST_Utils

class Preprocessor(object):
    def __init__(self, netcdf_dir, geotiff_dir):
        if netcdf_dir == None: netcdf_dir = 'netcdf_output/'
        self.netcdf_dir = netcdf_dir
        if geotiff_dir == None: geotiff_dir = 'geotiff_output/'
        self.geotiff_dir = geotiff_dir
        self.tmp = 'tmp/'

        Utils.check_create_folder(self.netcdf_dir)
        Utils.check_create_folder(self.tmp)
        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

        t_utils = TEST_Utils(self.netcdf_dir, self.geotiff_dir)


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
    

    def split_geotiff(self, geotiff_dir, input_dir, polarization):
        #no pre-init
        print('## Splitting geotiffs...')
        os.makedirs(geotiff_dir, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(input_dir, '*.tif*')

        #Currently not used, drop completely alongside Utils.split_polarizations?
        for i, input_geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.split_polarizations(geotiff_dir, input_geotiff, polarization)
      

    def netcdf_to_geotiff(self, geotiff_dir, netcdf_dir, polarization):
        #no pre-init
        print('## Converting input files to geotiff...')
        os.makedirs(geotiff_dir, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(netcdf_dir, '*.nc')
        
        for i, input_file in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.extract_polarization_band(input_file, geotiff_dir, polarization)


    # def assign_crs(self, geotiff_dir, crs = 'EPSG:4326'):
    #     print(f'## Assigning crs as {crs}')
    #     os.makedirs(self.tmp, exist_ok = True)
    #     input_data_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')
        
    #     for i, data in enumerate(input_data_list):
    #         print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
    #         Utils.crs_assign(data, self.tmp + 'tmp.tif', crs)


    def warp_files_to_crs(self, geotiff_dir, crs):
        #no pre-init
        print('## Warping to CRS...')
        os.makedirs(self.tmp, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(geotiff_dir, '*.tif')

        for data in input_file_list:
            output_tif = self.tmp + os.path.basename(data)
            Utils.crs_warp(data, crs, output_tif)
        Utils.remove_folder(self.tmp)


    def remove_empty(self, geotiff_dir):
        #no pre-init
        print('## Removing empty files')
        input_feil_list = Utils.file_list_from_dir(geotiff_dir, '*.tif')
        
        for i, data in enumerate(input_feil_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_feil_list)), end = '\r')
            if Utils.find_empty_raster(data):
                print(f'## No data in {data}')
                os.remove(data)


    def change_resolution(self, geotiff_dir, x_size, y_size):
        #no pre-init
        print('## Resampling resolution')
        os.makedirs(self.tmp, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(geotiff_dir, '*.tif')

        tmp_output = self.tmp + 'tmp.tif'
        
        for i, geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.change_raster_resolution(geotiff, tmp_output, x_size, y_size)
        Utils.remove_folder(self.tmp)


    def sort_output(self, geotiff_dir, polarization, folder_name):
        
        #pre init: create sorted outputs
        #requires either an advanced pre init function or a constant repeat of check/create dir

        print('## Sorting polarization and orbital direction')
        denoised_tifs = Utils.file_list_from_dir(geotiff_dir, '*.tif')

        output = Utils.create_sorted_outputs(geotiff_dir, polarization, folder_name)

        for i, geotiff in enumerate(denoised_tifs):
            print('# ' + str(i+1) + ' / ' + str(len(denoised_tifs)), end = '\r')
            Utils.sort_outputs(geotiff, polarization, output)


    def realign_rasters(self, geotiff_dir):
        #pre_init: need reference_geotransform. Must happen before util starts!
        print('## Fixing pixel alignment')
        os.makedirs(self.tmp, exist_ok = True)
        input_data_list = Utils.file_list_from_dir(geotiff_dir, '*.tif')

        reference_geotransform = Utils.get_reference_geotransform(input_data_list)

        for i, raster_path in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            Utils.align_raster(raster_path, self.tmp + 'tmp.tif', reference_geotransform)
        Utils.remove_folder(self.tmp)


        #_________________experimental stuff____________________________________________________


    def tool_manager(self, tool, threads, kwargs = {}):


        pre_init_util = pre_init_dict.get(tool)
        if not pre_init_util == None:            
            kwargs = pre_init_util(kwargs)

        if threads == 1:
            self.start_singleproc(tool, kwargs)
        elif threads >1:
            self.start_multiproc(tool, threads, kwargs)
        else:
            raise Exception(f'## Thread var must contain number greater than 0. Got {threads}')
    

    def start_singleproc(self, tool, kwargs):
        input_file_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')

        #creation of tmp dir should always be left to the tool itself
        #the name of the dir should always be uuid4 based.
        tmp = os.makedirs(self.tmp, exist_ok = True)

        # should kwargs be supplied by self? In all likelyhood not.
        # or maybe the Utils class should provide them?
        # move preprocessing init to utils?

        for i, input_file in enumerate(input_file_list):
            # print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            print(kwargs)
            tool_dict[tool](input_file, **kwargs)
            sys.exit()
        Utils.remove_folder(self.tmp)


    def start_multiproc(self, tool, threads, kwargs):
        items = []
        for file in Utils.file_list_from_dir(self.geotiff_dir, '*.tif'):
            items.append((file, kwargs))
        
        for result in Pool.starmap(tool_dict[tool], items):
            print() #do something?
            #also use that multiproc. thing that lets you specify threads.


    def tool_printer(self, tool):
        print()
        #tool should somehow provide info for a print statement

tool_dict = {
    "split_geotiff": TEST_Utils.split_polarizations,
    "change_resolution": TEST_Utils.change_raster_resolution,
    "sort_outputs": TEST_Utils.create_sorted_outputs,
    "align_raster": TEST_Utils.align_raster,
    "warp_crs": TEST_Utils.crs_warp    
}   #TODO later add clipper, denoiser, snap executor and unit converter

#if util in dict, value is a preinit function which must be run before util.
pre_init_dict = {
    "align_raster": TEST_Utils.get_reference_geotransform,
    "sort_outputs": TEST_Utils.create_sorted_outputs
}