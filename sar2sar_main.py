#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tensorflow as tf
from glob import glob
import os
import argparse
import sys

class SAR2SAR(object):

    # SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864

    def SAR2SAR_main(input_data, output_dir, checkpoint_dir):

        print('## Starting SAR2SAR...')

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
