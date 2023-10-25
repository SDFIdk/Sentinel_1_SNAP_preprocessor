#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tensorflow as tf
from glob import glob
import os
import argparse
import sys
from osgeo import gdal
from flood_utils import Utils
from pathlib import Path
import numpy as np
import shutil
import rasterio as rio
import pickle

from sar2sar_model import sar2sar_denoiser


class Denoiser(object):
    def __init__(self, output_dir):

        self.output_dir = output_dir
        self.geotiff_output_dir = output_dir + 'unfinished_geotiffs/'
        self.tmp = output_dir + 'tmp/'
        self.denoised_geotiffs = output_dir + 'denoised_geotiffs/'
        self.checkpoint = 'checkpoint/'
        self.orbit_dir = 'orbit/'

        Utils.check_create_folder(self.tmp)

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

    def select_denoiser(self, denoise_mode, mean_dict):

        noisy_npy_folder = self.tmp + 'npy_files/'
        denoised_npy_folder = self.tmp + 'denoised_numpys/'
        os.makedirs(noisy_npy_folder, exist_ok = True)
        os.makedirs(denoised_npy_folder, exist_ok = True)

        if denoise_mode == 'SAR2SAR':
            print('## SAR2SAR mode selected')

            noisy_npy_folder = self.convert_to_npy(noisy_npy_folder, mean_dict = mean_dict)

            self.SAR2SAR_main(noisy_npy_folder, denoised_npy_folder)

            self.recreate_geotiff(denoised_npy_folder, mean_dict = mean_dict)

            Utils.remove_folder(noisy_npy_folder)
        else:
            print('## Mean filter mode selected')
        
            denoised_npy_folder = self.apply_mean_filter(denoised_npy_folder)

            self.recreate_geotiff(denoised_npy_folder)

        Utils.remove_folder(self.tmp)

    # SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864

    
    def get_mean_dict(self, mean_dict):

        with open(mean_dict, 'rb') as f:
            mean_dict = pickle.load(f) 

        return mean_dict
            

    def convert_to_npy(self, noisy_npy_folder, mean_dict = False):
        print('## Converting to .npy...')

        Path(noisy_npy_folder).mkdir(exist_ok = True, parents = True)
        input_data_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')

        if mean_dict: mean_dict = self.get_mean_dict(mean_dict)

        for i, geotiff in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            
            with rio.open(geotiff, 'r') as ds:
                nds = ds.read().squeeze()
            
            if mean_dict: 
                rescale_factor = mean_dict[os.path.basename(geotiff)[:-13]]
                nds = nds * rescale_factor

            savename = noisy_npy_folder + os.path.basename(geotiff.replace('.tif', '.npy')) 

            if os.path.exists(savename):
                os.remove(savename)
            np.save(savename, nds)
            ds = None
            nds = None

        return noisy_npy_folder    
    
    
    def apply_mean_filter(self, output_folder):
        import xarray as xr
        from xrspatial.focal import mean as xrs_mean

        input_file_list = Utils.file_list_from_dir(self.geotiff_output_dir, '*.tif')
        Path(output_folder).mkdir(exist_ok = True, parents = True)
        
        for i, data in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')

            xds = xr.open_dataset(data, engine = 'rasterio').to_array().squeeze()
            xds = xrs_mean(xds)

            savename = output_folder + os.path.basename(data).replace('.tif', '.npy')
            np.save(savename, xds.to_numpy())
            xds = None

        return output_folder
    

    def SAR2SAR_main(self, input_data, output_dir):

        print('## Starting SAR2SAR...')

        parser = argparse.ArgumentParser(description = '')
        parser.add_argument('--use_gpu', dest = 'use_gpu', type = int, default = 1, help = 'GPU flag. 1 = gpu, 0 = cpu')
        parser.add_argument('--output_dir', dest = 'output_dir', default = output_dir, help = 'test examples are saved here')
        parser.add_argument('--input_data', dest = 'input_data', default = input_data, help = 'data set for testing')
        parser.add_argument('--stride_size', dest = 'stride_size', type = int, default = 64, help = 'define stride when image dim exceeds 264')
        args = parser.parse_args()

        if not os.path.exists(output_dir):
                os.makedirs(output_dir)

        def denoiser_test(denoiser):
            input_data = args.input_data

            test_files = glob((input_data + '/*.npy').format('float32')) 
            denoiser.test(test_files, ckpt_dir = self.checkpoint, save_dir = output_dir, dataset_dir=input_data, stride=args.stride_size)

        if args.use_gpu:
            gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction = 0.9)

            with tf.compat.v1.Session(config = tf.compat.v1.ConfigProto(gpu_options = gpu_options)) as sess:
                model = sar2sar_denoiser(sess)
                denoiser_test(model)
        else:
            with tf.compat.v1.Session() as sess:
                model = sar2sar_denoiser(sess)
                denoiser_test(model)

        return
    

    def recreate_geotiff(self, denoised_npy, mean_dict = False):
        gdal.UseExceptions()
        print('## Recreating geotiffs from .npy...')
        if mean_dict: mean_dict = self.get_mean_dict(mean_dict)

        npy_file_list = Utils.file_list_from_dir(denoised_npy, '*.npy')
        Path(self.tmp + 'denoised_geotiffs').mkdir(exist_ok = True, parents = True)

        for i, npy_file in enumerate(npy_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(npy_file_list)), end = '\r')            

            original_geotiff_path = npy_file.replace('.npy', '.tif').replace('tmp/denoised_numpys', 'unfinished_geotiffs')
            reconverted_geotiff_path = original_geotiff_path.replace('unfinished_geotiffs', 'tmp/denoised_geotiffs')

            original_dataset = gdal.Open(original_geotiff_path)
            if original_dataset is None:
                print("## Failed to open original GeoTIFF")
                continue

            reconverted_array = np.load(npy_file)

            if mean_dict: 
                rescale_factor = mean_dict[os.path.basename(original_geotiff_path)[:-13]]
                reconverted_array = reconverted_array / rescale_factor

            driver = gdal.GetDriverByName("GTiff")
            reconverted_dataset = driver.Create(
                reconverted_geotiff_path,
                reconverted_array.shape[1],
                reconverted_array.shape[0],
                original_dataset.RasterCount,
                original_dataset.GetRasterBand(1).DataType
            )

            reconverted_dataset.SetProjection(original_dataset.GetProjection())
            reconverted_dataset.SetGeoTransform(original_dataset.GetGeoTransform())

            for band_index in range(original_dataset.RasterCount):
                reconverted_band = reconverted_dataset.GetRasterBand(band_index + 1)
                reconverted_band.WriteArray(reconverted_array)

            original_dataset = None
            reconverted_dataset = None

            shutil.move(reconverted_geotiff_path, original_geotiff_path)

        return 