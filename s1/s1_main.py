import sys
from osgeo import gdal  #for some reason it crashes if imported in other modules????

from s1.s1_main import S1Preprocessor
from s1.denoiser import Denoiser
from s1.snap_converter import SnapPreprocessor
from s1.tool_manager import ToolManager

if __name__== '__main__':

    working_dir = 'D:/working_dir/ribe_2024_01_22/'
    safe_dir = 'D:/s1_raw_data/ribe_2024_01_22/'
    shape = 'ribe_aoi/ribe_aoi.shp'

    netcdf_dir = working_dir + 'netcdf/'
    geotiff_dir = working_dir + 'geotiff_dir/'

    pre_process_graph = 'snap_graphs/preprocessing_workflow_2023_no_cal_incidence.xml'
    gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe'
    crs = 'EPSG:25832'              # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 
    polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid

    s1_preprocessor = S1Preprocessor(
        working_dir = working_dir,
        safe_dir = safe_dir,
        netcdf_dir = netcdf_dir,
        geotiff_dir = geotiff_dir,
        pre_process_graph = pre_process_graph,
        gpt_exe = gpt_exe,
        crs = crs,
        polarization = polarization,
        shape = shape,
    )


class S1Preprocessor:

    def __init__(self, **kwargs):
        self.safe_dir = kwargs['safe_dir']
        self.crs = kwargs['crs']
        self.shape = kwargs['shape']
        self.gpt_exe = kwargs['gpt_exe']
        self.pre_process_graph = kwargs['pre_process_graph']
        self.threads = kwargs.get('threads', 1)
        self.denoise_mode = kwargs.get('denoise_mode', 'SAR2SAR')
        self.polarization = kwargs.get('polarization', ['VV', 'VH'])

    def s1_workflow(self):
        # safe_utils = ToolManager(safe_dir, '*.zip', 1) #TODO implement SAFE executor into Utils
        netcdf_utils = ToolManager(netcdf_dir, '*.nc', threads = 1, polarization=polarization)
        geotiff_utils = ToolManager(geotiff_dir, '*.tif', threads = 1, polarization=polarization)
        denoiser = Denoiser(geotiff_dir, shape)
        snap_executor = SnapPreprocessor(gpt_path=gpt_exe)


        import os # This needs to be removed somehow
        dataset_name = os.path.basename(os.path.normpath(safe_dir)) # This needs to be removed somehow

        snap_executor.graph_processing(safe_dir, netcdf_dir, pre_process_graph, input_ext='.zip')

        netcdf_utils.util_starter('netcdf_to_geotiff', output_dir = geotiff_dir)
        geotiff_utils.util_starter('clip_256', shape = shape, crs = crs)
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
        geotiff_utils = ToolManager(geotiff_dir, '*.tif', threads = 1, polarization=polarization)
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