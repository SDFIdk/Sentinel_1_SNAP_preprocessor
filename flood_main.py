import sys
from osgeo import gdal  #for some reason it crashes if imported in other modules????

from denoiser import Denoiser
from clip_256 import Clipper
from snap_converter import SnapPreprocessor
import unit_converter
from tool_manager import ToolManager
from tool_manager_init_test import Tool_manager_init_test

if __name__== '__main__':

    safe_dir = 'D:/s1_raw_data/ribe_2024_01_22/'
    shape = 'ribe_aoi/ribe_aoi.shp'

    # safe_dir = 'D:/s1_raw_data/skjern_2024_01_22/'
    # shape = "shapes/skjern/layers/POLYGON.shp"

    # safe_dir = 'D:/s1_raw_data/sneum_aa_2024_01_22/'
    # shape = "shapes/sneum_aa/layers/POLYGON.shp"
    
#     safe_dir = 'D:/s1_raw_data/varde_2024_01_22/'
#     shape = "shapes/varde/layers/POLYGON.shp"


#     netcdf_dir = 'D:/s1_netcdf_out/'
#     geotiff_dir = 'D:/s1_geotiff_out/'

    netcdf_dir = 'input/'
    geotiff_dir = 'output/'

    # safe_dir = 'D:/s1_test_safe/'
    # netcdf_dir = 'D:/s1_test_nc/'
    # geotiff_dir = 'D:/s1_test_geotiff/'

    # shape = 'D:/shapes/holstebro/POLYGON.shp'  # path to .shp file in unzipped shape dir
    # shape = 'D:/shapes/kolding/POLYGON.shp'
    # shape = 'D:/shapes/stavis_odense/POLYGON.shp'

    pre_process_graph = 'snap_graphs/preprocessing_workflow_2023_no_cal_incidence.xml'
    # safe_converter_graph = 'snap_graphs/extended_safe_to_geotiff.xml'
    #xml file with SNAP preprocessing stack. 

    gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe'
                                    # Path to SNAPs gpt.exe. SNAP is required for this program to run.

    crs = 'EPSG:25832'              # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 

    polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid

    # denoise_mode = 'SAR2SAR'        # if 'SAR2SAR', script will use ML based denoising.
    # denoise_mode = 'mean'
    # denoise_mode = 'SAR2SAR_mean_dict'


# safe_utils = Tool_manager_init_test(safe_dir, '*.zip', 1) #TODO implement SAFE executor into Utils
netcdf_utils = Tool_manager_init_test(netcdf_dir, '*.nc', threads = 1, polarization=polarization)
geotiff_utils = Tool_manager_init_test(geotiff_dir, '*.tif', threads = 1, polarization=polarization)

# -------------- init_test ----------------
# test_tool_manager = Tool_manager_init_test('output/', '*.tif', 1)
# test_tool_manager.util_starter('TEST_FUNK', a = '1', b = '2', c = '3')
# test_tool_manager.util_starter('TEST_FUNK')
# test_tool_manager.util_starter('align_raster')
# test_tool_manager.util_starter('copy_dir', copy_dir = 'TEST_DIRECTORY/')
# -------------- init_test ----------------

clipper = Clipper(geotiff_dir)
denoiser = Denoiser(geotiff_dir, shape)
snap_executor = SnapPreprocessor(gpt_path=gpt_exe)

# preprocessor.self_check(crs, polarization, denoise_mode)
# TODO check for checkpoint folder (SAR2SAR) 
# TODO check that gpt exe points to SNAP
# TODO check for files in netcdf and geotiff folders, ask for delete?


import os # This needs to be removed somehow
dataset_name = os.path.basename(os.path.normpath(safe_dir)) # This needs to be removed somehow

snap_executor.graph_processing(safe_dir, netcdf_dir, pre_process_graph, input_ext='.zip')

netcdf_utils.util_starter('netcdf_to_geotiff', output_dir = geotiff_dir)
clipper.start_clipper(input_dir=geotiff_dir, shape=shape, crs=crs)
geotiff_utils.util_starter('copy_dir', copy_dir = 'D:/s1_geotiff_out_not_denoised_/')

# ---------------------------------- SAR2SAR_track ----------------------------------
denoise_mode = 'SAR2SAR' # This needs to be removed somehow
denoiser.select_denoiser(denoise_mode, to_intensity = False)
# TODO fix (and locate) warnings about TF deprecations
# BUG enable GPU properly

geotiff_utils.util_starter('change_resolution', x_sixe = 10, y_sixe = 10)
geotiff_utils.util_starter('convert_unit', source_unit = 'linear', desitnation_unit = 'decibel')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_10m/')

geotiff_utils.util_starter('convert_unit', source_unit = 'decibel', desitnation_unit = 'power')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_10m/')

geotiff_utils.util_starter('convert_unit', source_unit = 'power', desitnation_unit = 'linear')
geotiff_utils.util_starter('change_resolution', x_sixe = 20, y_sixe = 20)

geotiff_utils.util_starter('convert_unit', source_unit = 'linear', desitnation_unit = 'decibel')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_20m/')

geotiff_utils.util_starter('convert_unit', source_unit = 'decibel', desitnation_unit = 'power')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_20m/')

# ---------------------------------- mean_track ----------------------------------
geotiff_dir = 'D:/s1_geotiff_out_not_denoised/'
geotiff_utils = Tool_manager_init_test(geotiff_dir, '*.tif', threads = 1, polarization=polarization)
denoise_mode = 'mean'
denoiser.select_denoiser(denoise_mode, to_intensity = False)

geotiff_utils.util_starter('change_resolution', x_sixe = 10, y_sixe = 10)
geotiff_utils.util_starter('convert_unit', source_unit = 'linear', desitnation_unit = 'decibel')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_10m/')

geotiff_utils.util_starter('convert_unit', source_unit = 'decibel', desitnation_unit = 'power')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_10m/')

geotiff_utils.util_starter('convert_unit', source_unit = 'power', desitnation_unit = 'linear')
geotiff_utils.util_starter('change_resolution', x_sixe = 20, y_sixe = 20)

geotiff_utils.util_starter('convert_unit', source_unit = 'linear', desitnation_unit = 'decibel')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_20m/')

geotiff_utils.util_starter('convert_unit', source_unit = 'decibel', desitnation_unit = 'power')
geotiff_utils.util_starter('align_raster')
geotiff_utils.util_starter('sort_output', output_path = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_20m/')

import shutil
# shutil.rmtree(geotiff_dir)

# ----------------------------------- OLD TOOL MANAGER ---------------------------------------
sys.exit()
snap_executor.graph_processing(safe_dir, netcdf_dir, pre_process_graph, input_ext='.zip')

ToolManager.util_starter('netcdf_to_geotiff', 1, {
        'input_dir':netcdf_dir,
        'output_dir':geotiff_dir,
        'polarization':polarization
        })

clipper.start_clipper(input_dir=geotiff_dir, shape=shape, crs=crs)
ToolManager.util_starter('remove_empty', 1, {
        'input_dir':geotiff_dir,
        })

ToolManager.util_starter('copy_dir', 1, {
        'input_dir':geotiff_dir,
        'copy_dir':'D:/s1_geotiff_out_not_denoised_/'
        })

# ---------------------------------- SAR2SAR_track ----------------------------------

denoise_mode = 'SAR2SAR'
denoiser.select_denoiser(denoise_mode, to_intensity = False)
# TODO fix (and locate) warnings about TF deprecations
# BUG enable GPU properly


ToolManager.util_starter('change_resolution', 1, {
        'input_dir':geotiff_dir,
        'x_size':10, 
        'y_size':10
        })

unit_converter.convert_unit(geotiff_dir, 'linear', 'decibel')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_10m/', 
        'polarization':polarization
        })

unit_converter.convert_unit(geotiff_dir, 'decibel', 'power')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_10m/', 
        'polarization':polarization
        })

unit_converter.convert_unit(geotiff_dir, 'power', 'linear')

ToolManager.util_starter('change_resolution', 1, {
        'input_dir':geotiff_dir,
        'x_size':20, 
        'y_size':20
        })

unit_converter.convert_unit(geotiff_dir, 'linear', 'decibel')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_20m/', 
        'polarization':polarization
        })

unit_converter.convert_unit(geotiff_dir, 'decibel', 'power')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_20m/', 
        'polarization':polarization
        })

# ---------------------------------- mean_track ----------------------------------

geotiff_dir = 'D:/s1_geotiff_out_not_denoised/'
denoise_mode = 'mean'
denoiser.select_denoiser(denoise_mode, to_intensity = False)
# TODO fix (and locate) warnings about TF deprecations
# BUG enable GPU properly


ToolManager.util_starter('change_resolution', 1, {
        'input_dir':geotiff_dir,
        'x_size':10, 
        'y_size':10
        })

unit_converter.convert_unit(geotiff_dir, 'linear', 'decibel')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_10m/', 
        'polarization':polarization
        })

unit_converter.convert_unit(geotiff_dir, 'decibel', 'power')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_10m/', 
        'polarization':polarization
        })

unit_converter.convert_unit(geotiff_dir, 'power', 'linear')

ToolManager.util_starter('change_resolution', 1, {
        'input_dir':geotiff_dir,
        'x_size':20, 
        'y_size':20
        })

unit_converter.convert_unit(geotiff_dir, 'linear', 'decibel')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_20m/', 
        'polarization':polarization
        })

unit_converter.convert_unit(geotiff_dir, 'decibel', 'power')

ToolManager.util_starter('align_raster', 1, {
        'input_dir':geotiff_dir,
        'tmp_dir': 'tmp/', 
        })

ToolManager.util_starter('sort_output', 1, {
        'input_dir':geotiff_dir,
        'output_path': f'{dataset_name}_{denoise_mode}_denoised_geotiffs_power_transform_20m/', 
        'polarization':polarization
        })

# import shutil
# shutil.rmtree(geotiff_dir)