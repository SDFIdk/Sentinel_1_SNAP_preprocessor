from osgeo import gdal
import sys
import os
from flood_utils import Utils
from multiprocessing.pool import Pool
from flood_utils_ditest import TEST_Utils

class Tool_manager(object):
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
        
        #possibly shouldnt be here
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


    def util_starter(self, tool, threads, kwargs = {}):

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
        input_file_list = Utils.file_list_from_dir(self.geotiff_dir, ['*.tif', '*.nc', '*.zip'])

        #creation of tmp dir should always be left to the tool itself
        #the name of the dir should always be uuid4 based.
        tmp = os.makedirs(self.tmp, exist_ok = True)

        for i, input_file in enumerate(input_file_list):
            # print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            print(kwargs)
            tool_dict[tool](input_file, **kwargs)
            sys.exit()
        Utils.remove_folder(self.tmp)


    def start_multiproc(self, tool, threads, kwargs):
        items = []
        for input_file in Utils.file_list_from_dir(self.geotiff_dir, ['*.tif', '*.nc', '*.zip']):
            items.append((input_file, kwargs))
        
        for result in Pool.starmap(tool_dict[tool], items):
            print() #?
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