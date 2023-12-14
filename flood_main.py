import sys
from flood_preprocessing import Preprocessor
from denoiser import Denoiser
from clip_256 import Clipper
from snap_converter import SNAP_preprocessor
import unit_converter

if __name__== '__main__':

    safe_dir = 'D:/s1_raw_data/holstebro_2015_12_07/'
    # safe_dir = 'D:/s1_raw_data/holstebro_2022_12_31/'
    # safe_dir = 'D:/s1_raw_data/kolding_2020_02_17/'
    # safe_dir = 'D:/s1_raw_data/stavis_odense_2022_02_21/'

    netcdf_dir = 'netcdf/'
    geotiff_dir = 'D:/s1_geotiff_out/'

    # safe_dir = 'D:/s1_test_safe/'
    # netcdf_dir = 'D:/s1_test_nc/'
    # geotiff_dir = 'D:/s1_test_geotiff/'


    shape = 'D:/shapes/holstebro/POLYGON.shp'  # path to .shp file in unzipped shape dir
    # shape = 'D:/shapes/kolding/POLYGON.shp'
    # shape = 'D:/shapes/stavis_odense/POLYGON.shp'

    pre_process_graph = 'snap_graphs/preprocessing_workflow_2023_no_cal.xml'
    # safe_converter_graph = 'snap_graphs/extended_safe_to_geotiff.xml'
    #xml file with SNAP preprocessing stack. 

    gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe'
                                    # Path to SNAPs gpt.exe. SNAP is required for this program to run.

    crs = 'EPSG:25832'              # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 

    polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid

    # denoise_mode = 'SAR2SAR'        # if 'SAR2SAR', script will use ML based denoising.
    denoise_mode = 'mean'

    
preprocessor = Preprocessor(netcdf_dir, geotiff_dir)
clipper = Clipper(geotiff_dir)
denoiser = Denoiser(geotiff_dir, shape)
snap_executor = SNAP_preprocessor(gpt_path=gpt_exe)


# preprocessor.self_check(crs, polarization, denoise_mode)
# TODO check for checkpoint folder (SAR2SAR) 
# TODO check that gpt exe points to SNAP
# TODO check for files in netcdf and geotiff folders, ask for delete?

#------modular SNAP------

# snap_executor.graph_processing(safe_dir, netcdf_dir, pre_process_graph, output_ext='.nc', input_ext='.zip')
preprocessor.netcdf_to_geotiff(netcdf_dir, geotiff_dir, polarization)
clipper.start_clipper(input_dir=geotiff_dir, shape=shape, crs=crs)
denoiser.select_denoiser(denoise_mode, to_intensity = False)

# unit_converter.convert_unit('D:/s1_geotiff_out/', 'power', 'linear')
preprocessor.change_resolution(x_size=10, y_size=10)

unit_converter.convert_unit('D:/s1_geotiff_out/', 'linear', 'decibel')
preprocessor.realign_rasters()
preprocessor.sort_output(polarization, 'holstebro_2015_mean_denoised_geotiffs_decibel_10m/')

unit_converter.convert_unit('D:/s1_geotiff_out/', 'decibel', 'power')
preprocessor.realign_rasters()
preprocessor.sort_output(polarization, 'holstebro_2015_mean_denoised_geotiffs_power_transform_10m/')

#------modular SNAP------


# snap_executor.graph_processing(safe_dir, geotiff_dir, pre_process_graph, output_ext='.nc', input_ext='.zip')

# preprocessor.netcdf_to_geotiff(netcdf_dir, geotiff_dir, polarization)

# clipper.start_clipper(input_dir=geotiff_dir + 'unfinished_geotiffs/', shape=shape, crs=crs)

# preprocessor.split_geotiff( output_dir, polarization)

# preprocessor.change_resolution(x_size=10, y_size=10)

# unit_converter.convert_unit('D:/s1_geotiff_out/unfinished_geotiffs/', 'decibel', 'linear')

# denoiser.select_denoiser(denoise_mode)
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