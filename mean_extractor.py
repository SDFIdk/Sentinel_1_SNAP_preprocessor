import os
from glob import glob
from pathlib import Path
from osgeo import gdal
import zipfile
import shutil
from snap_converter import SNAP_preprocessor
from pprint import pprint
import sys


class Correction_dict(object):
    def __init__(self, safe_dir, shape, tmp_dir, example_dir):
        self.tmp_dir = tmp_dir + 'mean_dict_tmp/'
        self.safe_dir = safe_dir
        self.shape = shape
        self.filename_example_dir = example_dir
        gdal.UseExceptions()


    def unzip_data_to_dir(self, zipped_data, output_dir):
        with zipfile.ZipFile(zipped_data, 'r') as zip_ref:
            zip_ref.extractall(output_dir)


    def open_safe_to_tmp(self, safe_file):
        self.unzip_data_to_dir(safe_file, self.tmp_dir)
        safe_data = glob(self.tmp_dir + '/*')[0]
        gdal_safe = gdal.Open(safe_data + '/manifest.safe', gdal.GA_ReadOnly)
        return gdal_safe
    

    def get_orbit_pol_info(self, gdal_safe, band):
        orbit = gdal_safe.GetMetadata().get('ORBIT_DIRECTION', '')
        if orbit == 'ASCENDING': orbit_direction = 'ASC'
        elif orbit == 'DESCENDING': orbit_direction = 'DSC'
        band_type = band.GetMetadata().get('POLARIZATION', '')
        return band_type + '_' + orbit_direction
    

    def log_to_mean_dict(self, safe_file, mean_dict):
        Path(self.tmp_dir).mkdir(exist_ok = True)

        gdal_safe = self.open_safe_to_tmp(safe_file)

        for band_index in range(1, gdal_safe.RasterCount + 1):
            band = gdal_safe.GetRasterBand(band_index)
            band_info = self.get_orbit_pol_info(gdal_safe, band)

            if 'VV' not in band_info and 'VH' not in band_info: 
                continue

            filename = os.path.basename(safe_file).replace('.zip', '_') + band_info + "_band.tif"
            output_geotiff = os.path.join(self.tmp_dir, filename)

            translate_options = gdal.TranslateOptions(
                format = "GTiff",
                bandList = [band_index],
                options = ["TILED=YES", "COMPRESS=None"],
                outputType = gdal.GDT_Int16
            )
            gdal.Translate(output_geotiff, gdal_safe, options=translate_options)

            SNAP_preprocessor.single_file_safe_preprocessing(safe_dir, 'snap_graphs/preprocessing_workflow_2023_lsm.xml', output_geotiff, 'land_sea_mask.xml')


            assert filename not in mean_dict, f"## {filename} already in dict! Check for duplicate input files"
            mean_dict[filename] = self.get_mean_from_shape_extent(output_geotiff, 'input/CLIP_TEST_OUT.tif')

        gdal_safe = None
        output_geotiff = None
        self.remove_unzipped_safe(self.tmp_dir)
        return mean_dict


    def remove_unzipped_safe(self, unzipped_safe):
        shutil.rmtree(unzipped_safe)


    def get_mean_from_shape_extent(self, output_geotiff, output_path):
        warp_options = gdal.WarpOptions(cutlineDSName = self.shape, cropToCutline = True)
        result = gdal.Warp(output_path, output_geotiff, options=warp_options)
        
        band = result.GetRasterBand(1)
        data = band.ReadAsArray(0, 0, result.RasterXSize, result.RasterYSize)
        return data.mean()  
    

    def populate_correction_dict(self):
        print('## Creating correction factors for SAR2SAR')
        mean_dict = {}

        safe_files = glob(self.safe_dir + '*.zip')

        for i, safe_file in enumerate(safe_files):
            print('# ' + str(i+1) + ' / ' + str(len(safe_files)), end = '\r')
            mean_dict = self.log_to_mean_dict(safe_file, mean_dict)
        return mean_dict
    
if __name__ == "__main__":
    safe_dir = 'safe_dir/'

    shapefile_path = 'ribe_aoi/ribe_aoi.shp'
    # shapefile_path = 'syddanmark_stormflod/POLYGON.shp'
    filename_example_dir = 'example/'

    from mean_extractor import Mean_dict
    correction_finder = Mean_dict(safe_dir = safe_dir, shape = shapefile_path)
    mean_dict = correction_finder.populate_correction_dict(filename_example_dir)