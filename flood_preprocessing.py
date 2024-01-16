from osgeo import gdal
import sys
import os
from flood_utils import Utils
from multiprocessing.pool import Pool

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
    

    def split_geotiff(self, input_dir, polarization):
        print('## Splitting geotiffs...')

        os.makedirs(self.geotiff_dir, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(input_dir, '*.tif*')
        for i, input_geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.split_polarizations(self.geotiff_dir, input_geotiff, polarization)
      

    def netcdf_to_geotiff(self, netcdf_dir, geotiff_dir, polarization):
        print('## Converting input files to geotiff...')
            
        os.makedirs(geotiff_dir, exist_ok = True)
        input_file_list = Utils.file_list_from_dir(netcdf_dir, '*.nc')
        
        for i, input_file in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.extract_polarization_band(input_file, self.geotiff_dir, polarization)


    def assign_crs(self, crs = 'EPSG:4326'):
        print(f'## Assigning crs as {crs}')
        os.makedirs(self.tmp, exist_ok = True)
        tmp_output = self.tmp + 'tmp.tif'

        input_data_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')
        
        for i, data in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            Utils.crs_assign(data, tmp_output, crs)


    def warp_files_to_crs(self, crs):
        print('## Warping to CRS...')

        input_data_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')
        os.makedirs(self.tmp, exist_ok = True)
        
        for data in input_data_list:
            output_tif = self.tmp + os.path.basename(data)
            Utils.crs_warp(data, crs, output_tif)
        Utils.remove_folder(self.tmp)


    def remove_empty(self):
        print('## Removing empty files')
        input_data_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')
        
        for i, data in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            if Utils.find_empty_raster(data):
                print(f'## No data in {data}')
                os.remove(data)


    def change_resolution(self, x_size, y_size):
        print('## Resampling resolution')
        os.makedirs(self.tmp, exist_ok = True)
        tmp_output = self.tmp + 'tmp.tif'

        input_data_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')
        
        for i, geotiff in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            Utils.change_raster_resolution(geotiff, tmp_output, x_size, y_size)


    def sort_output(self, polarization, folder_name):
        print('## Sorting polarization and orbital direction')

        if not isinstance(polarization, list):
            polarization = [polarization]
        output = Utils.create_sorted_outputs(self.geotiff_dir, polarization, folder_name)

        denoised_tifs = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')
        for i, tif in enumerate(denoised_tifs):
            print('# ' + str(i+1) + ' / ' + str(len(denoised_tifs)), end = '\r')
            Utils.sort_outputs(tif, polarization, output)


    def realign_rasters(self):
        print('## Fixing pixel alignment')
        input_file_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')

        reference_geotransform = Utils.get_reference_geotransform(input_file_list)

        os.makedirs(self.tmp, exist_ok = True)
        for i, raster_path in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            Utils.align_raster(raster_path, self.tmp + 'tmp.tif', reference_geotransform)


# _____________________________________________________________________________________


    def tool_manager(self, tool, threads, kwargs):
        if threads == 1:
            self.start_singleproc(tool, kwargs)
        elif threads >1:
            self.start_multiproc(tool, threads, kwargs)
        else:
            raise Exception(f'## Thread var must contain number greater than 0. Got {threads}')
    

    def start_singleproc(self, tool, kwargs):
        input_file_list = Utils.file_list_from_dir(self.geotiff_dir, '*.tif')

        self.tool_printer(tool)
        tmp = os.makedirs(self.tmp, exist_ok = True)

        for i, input_file in enumerate(input_file_list):
            tool_dict[tool](input_file, **kwargs)
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')


    def start_multiproc(self, tool, threads, kwargs):

        items = []
        for file in Utils.file_list_from_dir(self.geotiff_dir, '*.tif'):
            items.append((file, kwargs))
        
        for result in Pool.starmap(tool_dict[tool], items):
            print() #do something?


    def tool_printer(self, tool):
        print()
        #tool should somehow provide info for a print statement

tool_dict = {
    "split geotiff": Utils.split_polarizations,
    "change resolution": Utils.change_raster_resolution,
    "sort outputs": Utils.create_sorted_outputs,
    "align pixels": Utils.align_raster,
    "warp crs": Utils.crs_warp    
}   #TODO later add clipper, denoiser, snap executor and unit converter