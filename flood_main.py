import sys
from flood_preprocessing import Preprocessor
from denoiser import Denoiser
from clip_256 import Clipper
from snap_converter import SNAP_preprocessor
import unit_converter

if __name__== '__main__':

    safe_dir = 'D:/s1_raw_data/holstebro_2015_12_07/'
    netcdf_dir = 'D:/s1_test_nc/'
    output_dir = 'D:/s1_geotiff_out/'

    # safe_dir = 'safe_test/'
    # output_dir = 'D:/s1_test_geotiff/'

    # netcdf_dir = 'input/'
    # output_dir = 'output/
    # input/output will be created if not present

    shape = 'D:/shapes/holstebro/POLYGON.shp'  # path to .shp file in unzipped shape dir

    snap_graph = 'snap_graphs/preprocessing_workflow_2023_lsm.xml'
    #xml file with SNAP preprocessing stack. 
    # TODO ensure xml is available on github!

    gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe'
                                    # Path to SNAPs gpt.exe. SNAP is required for this program to run.

    crs = 'EPSG:25832'              # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 

    polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid

    denoise_mode = 'SAR2SAR'        # if 'SAR2SAR', script will use ML based denoising.
    # denoise_mode = 'mean'

    
preprocessor = Preprocessor(netcdf_dir, output_dir)
clipper = Clipper(output_dir)
denoiser = Denoiser(output_dir, safe_dir, shape)

# preprocessor.self_check(crs, polarization, denoise_mode)
# TODO check for checkpoint folder (SAR2SAR) 
# TODO check that gpt exe points to SNAP

SNAP_preprocessor.safe_preprocessing(safe_dir, snap_graph, netcdf_dir, gpt_exe)

preprocessor.convert_to_geotiff(polarization)

# preprocessor.change_resolution(x_res=10, y_res=10)

# clipper.start_clipper(shape, crs)

# unit_converter.convert_unit('D:/s1_geotiff_out/unfinished_geotiffs/', 'decibel', 'linear')

# denoiser.select_denoiser(denoise_mode, mean_dict)
# TODO fix (and locate) warnings about TF deprecations
# BUG enable GPU properly
#   tensorflow may need to be rewritten entirely
# SAR2SAR may need to be recreated entirely to comply with tf v2

# unit_converter.convert_unit('D:/s1_geotiff_out/unfinished_geotiffs/', 'linear', 'decibel')

# preprocessor.warp_files_to_crs(crs)
# # BUG possibly deprecated now
# # TODO crate gdal options in Preprocessing without gdal. Pass string somehow? 
# #   import gdaloptions as gdalopts ? only imports single thing, should be more efficient

# preprocessor.change_resolution(x_res=10, y_res=10)
# preprocessor.realign_rasters()

# clipper.start_clipper(shape, crs)
# preprocessor.sort_output(polarization, 'ribe_sar2sar_denoised_geotiffs_power/')

# unit_converter.convert_unit('D:/s1_geotiff_out/unfinished_geotiffs/', 'power', 'decibel')
# clipper.start_clipper(shape, crs)
# preprocessor.sort_output(polarization, 'ribe_sar2sar_denoised_geotiffs_decibel/')

# unit_converter.convert_unit('D:/s1_geotiff_out/unfinished_geotiffs/', 'decibel', 'power')