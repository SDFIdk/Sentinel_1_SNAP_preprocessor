from osgeo import gdal #BUG #CURSED has to be on top, otherwise "No module named _gdal" ??? 
import tensorflow as tf
from glob import glob
import os
import argparse
import sys
from pathlib import Path
import numpy as np
import shutil
import rasterio as rio

from sentinel_1.utils import Utils
from sentinel_1.sar2sar_model import sar2sar_denoiser
from sentinel_1.mean_extractor import Correction_dict


class Denoiser(object):
    def __init__(self, geotiff_dir, shapefile_path):
        self.geotiff_dir = geotiff_dir
        self.tmp = geotiff_dir + "tmp/"
        self.checkpoint = "sentinel_1/checkpoint/"
        self.orbit_dir = "orbit/"
        self.shape = shapefile_path
        self.gpt_exe = "snap_graphs/land_sea_mask.xml"

        Utils.check_create_folder(self.tmp)

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

    def select_denoiser(self, denoise_mode, to_intensity=False):
        denoised_npy = self.tmp + "denoised_numpys/"
        Path(self.tmp + "denoised_geotiffs").mkdir(exist_ok=True, parents=True)

        if denoise_mode == "SAR2SAR":
            # SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864
            print("## SAR2SAR mode selected")

            noisy_npy_folder = self.convert_to_npy(
                mean_dict=None, to_intensity=to_intensity
            )
            self.SAR2SAR_main(noisy_npy_folder, denoised_npy)
            self.recreate_geotiff(denoised_npy, to_amplitude=to_intensity)

            Utils.remove_folder(noisy_npy_folder)
        elif denoise_mode == "SAR2SAR_mean_dict":
            print("## SAR2SAR mean dict mode selected (experimental)")

            correction_finder = Correction_dict(
                safe_dir=self.safe_dir,
                shape=self.shape,
                tmp_dir=self.tmp,
                example_dir=self.geotiff_output_dir,
                gpt_path=self.gpt_exe,
            )
            mean_dict = correction_finder.populate_correction_dict()

            noisy_npy_folder = self.convert_to_npy(mean_dict=mean_dict)
            self.SAR2SAR_main(noisy_npy_folder, denoised_npy)
            self.recreate_geotiff(denoised_npy, mean_dict)

            Utils.remove_folder(noisy_npy_folder)
        else:
            print("## Mean filter mode selected")
            self.apply_mean_filter(output_folder=denoised_npy)
            self.recreate_geotiff(denoised_npy)

        Utils.remove_folder(self.tmp)

    def convert_to_npy(self, mean_dict=False, to_intensity=False):
        print("## Converting to .npy...")

        noisy_npy_folder = self.tmp + "npy_files/"
        os.makedirs(noisy_npy_folder, exist_ok=True)

        input_data_list = Utils.file_list_from_dir(self.geotiff_dir, "*.tif")

        for i, geotiff in enumerate(input_data_list):
            print("# " + str(i + 1) + " / " + str(len(input_data_list)), end="\r")

            with rio.open(geotiff, "r") as ds:
                nds = ds.read().squeeze()

            if mean_dict:
                rescale_factor = mean_dict[os.path.basename(geotiff)]
                nds = nds * rescale_factor

            nds = np.sqrt(nds)
            if to_intensity:
                nds = nds**2

            savename = noisy_npy_folder + os.path.basename(
                geotiff.replace(".tif", ".npy")
            )

            if os.path.exists(savename):
                os.remove(savename)
            np.save(savename, nds)
            ds = None
            nds = None
        return noisy_npy_folder

    def apply_mean_filter(self, output_folder):
        import xarray as xr
        from xrspatial.focal import mean as xrs_mean

        os.makedirs(output_folder, exist_ok=True)

        input_file_list = Utils.file_list_from_dir(self.geotiff_dir, "*.tif")
        Path(output_folder).mkdir(exist_ok=True, parents=True)

        for i, data in enumerate(input_file_list):
            print("# " + str(i + 1) + " / " + str(len(input_file_list)), end="\r")

            xds = xr.open_dataset(data, engine="rasterio").to_array().squeeze()
            xds = xrs_mean(xds[0,:,:]) #Hardcoded to take first band which is assumed to be data band.

            savename = output_folder + os.path.basename(data).replace(".tif", ".npy")
            np.save(savename, xds.to_numpy())
            xds = None
        return output_folder

    def SAR2SAR_main(self, noisy_npy_folder, denoised_npy):
        print("## Starting SAR2SAR...")

        use_gpu = True
        stride = 32  # change to 32 to increase quality at cost of time

        if not os.path.exists(denoised_npy):
            os.makedirs(denoised_npy)

        def denoiser_starter(model, noisy_npy_folder):
            noisy_files = glob((noisy_npy_folder + "/*.npy").format("float32"))
            model.test(
                noisy_files,
                ckpt_dir=self.checkpoint,
                save_dir=denoised_npy,
                dataset_dir=noisy_npy_folder,
                stride=stride,
            )

        if use_gpu:
            gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.9)

            with tf.compat.v1.Session(
                config=tf.compat.v1.ConfigProto(gpu_options=gpu_options)
            ) as sess:
                model = sar2sar_denoiser(sess)
                denoiser_starter(model, noisy_npy_folder)
        else:
            with tf.compat.v1.Session() as sess:
                model = sar2sar_denoiser(sess)
                denoiser_starter(model, noisy_npy_folder)
        return


    # def recreate_geotiff(self, denoised_npy_dir, mean_dict=False, to_amplitude=False):
    #     gdal.UseExceptions()
    #     print("## Recreating geotiffs from .npy...")

    #     denoised_npy_files = Utils.file_list_from_dir(denoised_npy_dir, "*.npy")
    #     Path(self.tmp + "denoised_geotiffs").mkdir(exist_ok=True, parents=True)

    #     for i, denoised_npy_file in enumerate(denoised_npy_files):
    #         print("# " + str(i + 1) + " / " + str(len(denoised_npy_files)), end="\r")

    #         original_geotiff_path = denoised_npy_file.replace(".npy", ".tif").replace(
    #             "tmp/denoised_numpys", ""
    #         )
    #         tmp_densoised_geotiff = self.tmp + "tmp.tif"

    #         original_dataset = gdal.Open(original_geotiff_path)
    #         assert original_dataset, (
    #             "## Failed to open original GeoTIFF")

    #         denoised_nds = np.load(denoised_npy_file)

    #         if to_amplitude:
    #             denoised_nds = np.sqrt(
    #                 denoised_nds
    #             )
    #         if mean_dict:
    #             rescale_factor = mean_dict[os.path.basename(original_geotiff_path)]
    #             denoised_nds = denoised_nds / rescale_factor

    #         driver = gdal.GetDriverByName("GTiff")
    #         reconverted_dataset = driver.Create(
    #             tmp_densoised_geotiff,
    #             denoised_nds.shape[1],
    #             denoised_nds.shape[0],
    #             original_dataset.RasterCount,
    #             original_dataset.GetRasterBand(1).DataType,
    #         )

    #         reconverted_dataset.SetProjection(original_dataset.GetProjection())
    #         reconverted_dataset.SetGeoTransform(original_dataset.GetGeoTransform())

    #         for band_index in range(original_dataset.RasterCount):
    #             reconverted_band = reconverted_dataset.GetRasterBand(band_index + 1)
    #             reconverted_band.WriteArray(denoised_nds)

    #         original_dataset = None
    #         reconverted_dataset = None

    #         shutil.move(tmp_densoised_geotiff, original_geotiff_path)
    #     return


    def recreate_geotiff(self, denoised_npy_dir, mean_dict=False, to_amplitude=False):
        gdal.UseExceptions()
        print("## Recreating geotiffs from .npy...")

        denoised_npy_files = Utils.file_list_from_dir(denoised_npy_dir, "*.npy")
        Path(self.tmp + "denoised_geotiffs").mkdir(exist_ok=True, parents=True)

        for i, denoised_npy_file in enumerate(denoised_npy_files):
            print("# " + str(i + 1) + " / " + str(len(denoised_npy_files)), end="\r")

            original_geotiff_path = denoised_npy_file.replace(".npy", ".tif").replace(
                "tmp/denoised_numpys", ""
            )

            original_dataset = gdal.Open(original_geotiff_path, gdal.GA_Update)
            assert original_dataset, "## Failed to open original GeoTIFF"

            denoised_nds = np.load(denoised_npy_file)

            if to_amplitude:
                denoised_nds = np.sqrt(denoised_nds)
            if mean_dict:
                rescale_factor = mean_dict.get(os.path.basename(original_geotiff_path), 1)
                denoised_nds = denoised_nds / rescale_factor

            original_dataset.GetRasterBand(1).WriteArray(denoised_nds)
            original_dataset = None