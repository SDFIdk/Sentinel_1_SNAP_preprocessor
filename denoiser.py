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

class Denoiser(object):
    def __init__(self, output_dir):

        self.output_dir = output_dir
        self.geotiff_output_dir = output_dir + 'unfinished_geotiffs/'
        self.tmp = output_dir + 'tmp/'
        self.denoised_geotiffs = output_dir + 'denoised_geotiffs/'
        self.checkpoint = 'checkpoint/'
        self.orbit_dir = 'orbit/'

        Utils.check_create_folder(self.input_dir)
        Utils.check_create_folder(self.tmp)

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

    def select_denoiser(self, denoise_mode):

        # tmp_denoise_output = self.tmp
        noisy_npy_folder = self.tmp + 'npy_files/'
        denoised_npy_folder = self.tmp + 'denoised_numpys/'
        os.makedirs(noisy_npy_folder, exist_ok = True)
        os.makedirs(denoised_npy_folder, exist_ok = True)

        if denoise_mode == 'SAR2SAR':
            print('## SAR2SAR mode selected')

            # Denoiser.safe_normalize(self.geotiff_output_dir)

            noisy_npy_folder = Denoiser.convert_to_npy(self.geotiff_output_dir, noisy_npy_folder)
            Denoiser.SAR2SAR_main(noisy_npy_folder, denoised_npy_folder, self.checkpoint)

            # Denoiser.safe_denormalize(self.geotiff_output_dir)

            Utils.remove_folder(noisy_npy_folder)
        else:
            print('## Mean filter mode selected')
            denoised_npy_folder = Denoiser.apply_mean_filter(self.geotiff_output_dir, denoised_npy_folder)

        Denoiser.recreate_geotiff(denoised_npy_folder, self.geotiff_output_dir, self.tmp)

        Utils.remove_folder(self.tmp)

    # SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864

    def SAR2SAR_main(self, input_data, output_dir, checkpoint_dir):

        print('## Starting SAR2SAR...')

        pkl_file = Utils.file_list_from_dir('' + '*.pkl')
        if not pkl_file:
            print('## No mean data found for SAR2SAR!')
            sys.exit()

        parser = argparse.ArgumentParser(description = '')
        parser.add_argument('--use_gpu', dest = 'use_gpu', type = int, default = 1, help = 'GPU flag. 1 = gpu, 0 = cpu')
        parser.add_argument('--output_dir', dest = 'output_dir', default = output_dir, help = 'test examples are saved here')
        parser.add_argument('--input_data', dest = 'input_data', default = input_data, help = 'data set for testing')
        parser.add_argument('--stride_size', dest = 'stride_size', type = int, default = 64, help = 'define stride when image dim exceeds 264')
        args = parser.parse_args()

        if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir)
        from sar2sar_model import denoiser

        def denoiser_test(denoiser):
            input_data = args.input_data

            test_files = glob((input_data + '/*.npy').format('float32')) 
            denoiser.test(test_files, ckpt_dir=checkpoint_dir, save_dir=args.output_dir, dataset_dir=input_data, stride=args.stride_size)

        if args.use_gpu:
            gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction = 0.9)

            with tf.compat.v1.Session(config = tf.compat.v1.ConfigProto(gpu_options = gpu_options)) as sess:
                model = denoiser(sess)
                denoiser_test(model)
        else:
            with tf.compat.v1.Session() as sess:
                model = denoiser(sess)
                denoiser_test(model)

        return
    
    def get_mean_dict():
        # geotiff_files = Utils.file_list_from_dir(geotiff_dir + '*.tif')
        pkl_file = Utils.file_list_from_dir('' + '*.pkl')
        if not pkl_file:
            print('## No mean data found for SAR2SAR!')
            sys.exit()

        with open(pkl_file, 'rb') as f:
            mean_dict = pickle.load(f) 

        return mean_dict
            

    def convert_to_safe_norm_npy(self, input_folder, noisy_npy_folder):
        print('## Converting to .npy...')

        Path(noisy_npy_folder).mkdir(exist_ok = True, parents = True)
        input_data_list = Utils.file_list_from_dir(input_folder, '*.tif')
        mean_dict = Denoiser.get_mean_dict()

        for i, geotiff in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            
            safe_mean = mean_dict[os.path.splitext(geotiff)[0]]
            with rio.open(geotiff, 'r') as ds:
                nds = ds.read().squeeze()
                nds = nds * safe_mean

            savename = noisy_npy_folder + os.path.basename(geotiff.replace('.tif', '.npy')) 

            if os.path.exists(savename):
                os.remove(savename)
            np.save(savename, nds)
            ds = None
            nds = None

        return noisy_npy_folder    
    
    
    def convert_to_npy(self, input_folder, noisy_npy_folder):
        Path(noisy_npy_folder).mkdir(exist_ok = True, parents = True)
        input_data_list = Utils.file_list_from_dir(input_folder, '*.tif')

        print('## Converting to .npy...')

        for i, geotiff in enumerate(input_data_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_data_list)), end = '\r')
            with rio.open(geotiff, 'r') as ds:
                nds = ds.read().squeeze()

            savename = noisy_npy_folder + os.path.basename(geotiff.replace('.tif', '.npy')) 

            if os.path.exists(savename):
                os.remove(savename)
            np.save(savename, nds)
            ds = None
            nds = None

        return noisy_npy_folder
    
    
    def apply_mean_filter(self, geotiff_folder, output_folder):
        import xarray as xr
        from xrspatial.focal import mean as xrs_mean

        input_file_list = Utils.file_list_from_dir(geotiff_folder, '*.tif')
        Path(output_folder).mkdir(exist_ok = True, parents = True)
        
        for i, data in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')

            xds = xr.open_dataset(data, engine = 'rasterio').to_array().squeeze()
            xds = xrs_mean(xds)

            savename = output_folder + os.path.basename(data).replace('.tif', '.npy')
            np.save(savename, xds.to_numpy())
            xds = None

        return output_folder
    

    def recreate_geotiff(self, denoised_npy, original_geotiff_dir, denoise_tmp_output):
        gdal.UseExceptions()
        print('## Recreating geotiffs from .npy...')

        npy_file_list = Utils.file_list_from_dir(denoised_npy, '*.npy')
        Path(denoise_tmp_output + 'denoised_geotiffs').mkdir(exist_ok = True, parents = True)

        for i, npy_file in enumerate(npy_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(npy_file_list)), end = '\r')            

            original_geotiff_path = npy_file.replace('.npy', '.tif').replace('tmp/denoised_numpys', 'unfinished_geotiffs')
            reconverted_geotiff_path = original_geotiff_path.replace('unfinished_geotiffs', 'tmp/denoised_geotiffs')

            original_dataset = gdal.Open(original_geotiff_path)
            if original_dataset is None:
                print("## Failed to open original GeoTIFF")
                continue

            reconverted_array = np.load(npy_file)

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

        return original_geotiff_dir
