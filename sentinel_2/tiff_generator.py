import sys
import subprocess

# sys.path.append('Scripts/')
# import gdal_merge
import zipfile
import os
import shutil
import glob
from pathlib import Path
from osgeo import gdal
import pprint
import rasterio as rio


class Tiff_generator(object):
    def complete(text, state):
        return (glob.glob(text + "*") + [None])[state]

    def get_immediate_subdirectories(a_dir):
        return [
            name
            for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))
        ]

    def generate_geotiffs(input_product, output_path):
        basename = os.path.basename(input_product)
        safe_dir = os.path.join(output_path, basename[:-3] + "SAFE")

        zip = zipfile.ZipFile(input_product)
        zip.extractall(output_path)

        product_name = os.path.basename(input_product)[:-4]
        output_subdirectory = os.path.join(output_path, product_name + "_PROCESSED")
        Path(output_subdirectory).mkdir(exist_ok=True)

        sub_directories = Tiff_generator.get_immediate_subdirectories(
            safe_dir + "/GRANULE"
        )

        for granule in sub_directories:
            unprocessed_band = os.path.join(
                output_path, product_name + ".SAFE", "GRANULE", granule, "IMG_DATA"
            )
            Tiff_generator.generate_all_bands(
                unprocessed_band, granule, output_subdirectory, output_path
            )

        shutil.rmtree(safe_dir)
        shutil.rmtree(output_subdirectory)

    def generate_all_bands(unprocessed_band, granule, output_subdirectory, newout):
        granule_part_1 = unprocessed_band.split(".SAFE")[0][-22:-16]
        granule_part_2 = unprocessed_band.split(".SAFE")[0][-49:-34]
        granule_band_template = granule_part_1 + "_" + granule_part_2 + "_"

        if not os.path.exists(output_subdirectory + "/IMAGE_DATA"):
            os.makedirs(output_subdirectory + "/IMAGE_DATA")

        output_tiff = "/" + granule[:-6] + "16Bit-AllBands.tif"
        output_vrt = "/" + granule[:-6] + "16Bit-AllBands.vrt"

        geotiff_output = newout + output_tiff
        output_vrt = output_subdirectory + "/IMAGE_DATA/" + output_vrt
        input_path = unprocessed_band

        bands = {
            "band_AOT": input_path + "/R10m/" + granule_band_template + "AOT_10m.jp2",
            "band_02": input_path + "/R10m/" + granule_band_template + "B02_10m.jp2",
            "band_03": input_path + "/R10m/" + granule_band_template + "B03_10m.jp2",
            "band_04": input_path + "/R10m/" + granule_band_template + "B04_10m.jp2",
            "band_05": input_path + "/R20m/" + granule_band_template + "B05_20m.jp2",
            "band_06": input_path + "/R20m/" + granule_band_template + "B06_20m.jp2",
            "band_07": input_path + "/R20m/" + granule_band_template + "B07_20m.jp2",
            "band_08": input_path + "/R10m/" + granule_band_template + "B08_10m.jp2",
            "band_8A": input_path + "/R20m/" + granule_band_template + "B8A_20m.jp2",
            "band_09": input_path + "/R60m/" + granule_band_template + "B09_60m.jp2",
            "band_WVP": input_path + "/R10m/" + granule_band_template + "WVP_10m.jp2",
            "band_11": input_path + "/R20m/" + granule_band_template + "B11_20m.jp2",
            "band_12": input_path + "/R20m/" + granule_band_template + "B12_20m.jp2",
        }

        vrt_dataset = gdal.BuildVRT(
            output_vrt,
            list(bands.values()),
            separate=True,
            resolution="user",
            xRes=20,
            yRes=20,
        )

        for i, band_name in enumerate(bands, start=1):
            band = vrt_dataset.GetRasterBand(i)
            band.SetMetadataItem("DESCRIPTION", band_name)

        gdal.Translate(geotiff_output, vrt_dataset, format="GTiff")

        return geotiff_output
