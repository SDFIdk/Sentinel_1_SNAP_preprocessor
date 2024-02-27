from sentinel_1.utils import Utils

import rasterio as rio
import numpy as np
import os
from osgeo import gdal
import shutil

#check list in order of check:
#empty files
#resolution
#dynamic range
#

class FileQA:
    def __init__(self, result_dir):

        self.result_dir = result_dir
        self.log = []

    def check_empty(self, input_file):
        with rio.open(input_file) as src:
            data = src.read(1)

            if not np.all(np.isnan(data)): return
            
            os.remove(input_file)
            self.log.append((input_file, "No data"))
            return True

    def check_resolution(self, input_file):
        """
        Trims a dataset to a resolution divisible by 256
        """

        dataset = gdal.Open(input_file)

        original_width = dataset.RasterXSize
        original_height = dataset.RasterYSize

        new_width = (original_width // 256) * 256
        new_height = (original_height // 256) * 256

        if new_width == original_width and new_height == original_height:
            return
        else:
            # with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp:
            #     temp_output_path = tmp.name
            temp_output_path = "tmp.tif"
            driver = gdal.GetDriverByName("GTiff")
            out_dataset = driver.Create(
                temp_output_path,
                new_width,
                new_height,
                dataset.RasterCount,
                dataset.GetRasterBand(1).DataType,
            )
            out_dataset.SetGeoTransform(dataset.GetGeoTransform())
            out_dataset.SetProjection(dataset.GetProjection())

            for i in range(dataset.RasterCount):
                in_band = dataset.GetRasterBand(i + 1)
                out_band = out_dataset.GetRasterBand(i + 1)

                data = in_band.ReadAsArray(0, 0, new_width, new_height)
                out_band.WriteArray(data)
        dataset = None
        out_dataset = None
        out_band = None

        shutil.move(temp_output_path, input_file)
        self.log.append((input_file, "Bad resolution"))

    def check_range(self, input_file):
        """
        Adjust the first band of a GeoTIFF if its dynamic range exceeds a given interval.

        Parameters:
        input_tif_path (str): Path to the input GeoTIFF file.
        max_interval (int or float): The maximum allowed interval for the dynamic range.
        """

        if 'decibel' in input_file:
            unit = 'decibel'
            min_val = -10000
            max_val = 1000
        elif 'power' in input_file:
            unit = 'power'
            min_val = -10000
            max_val = 1000
        elif 'linear' in input_file:
            unit = 'linear'
            min_val = -10000
            max_val = 1000000
        
        with rio.open(input_file, 'r+') as dataset:
            band = dataset.read(1)

            values_within_thresholds = np.all((band >= min_val) & (band <= max_val))
            if not values_within_thresholds:

                band = band.clip(min_val, max_val)
                dataset.write(band, 1)
                self.log.append((input_file, f"Unit type {unit} contained values exceeding {min_val} - {max_val}"))

    def assure_files(self):

        check_files = Utils.file_list_from_dir(self.result_dir, "**/*.tif")

        for input_file in check_files:
            
            if self.check_empty(input_file): continue
            self.check_resolution(input_file)
            self.check_range

            log_name = os.path.basename(self.result_dir) + '.txt'
            log_path = os.path.join(self.result_dir, log_name)
            with open(log_path, 'w') as f:
                for line in self.log:
                    f.write(f"{line}\n")