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

gdal.UseExceptions()

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
        band_path = granule_part_1 + "_" + granule_part_2 + "_"

        if not os.path.exists(output_subdirectory + "/IMAGE_DATA"):
            os.makedirs(output_subdirectory + "/IMAGE_DATA")

        output_tiff = "/" + granule[:-6] + "16Bit-AllBands.tif"
        output_vrt = "/" + granule[:-6] + "16Bit-AllBands.vrt"

        geotiff_output = newout + output_tiff
        output_vrt = output_subdirectory + "/IMAGE_DATA/" + output_vrt
        granule = Path(unprocessed_band)


        # a = gdal.Open(granule / "R10m" / str(band_path + "AOT_10m.jp2"))
        # print(str(a.RasterCount))
        # metadata=a.GetMetadata()
        # print(metadata)

        # sys.exit()

        bands = {
            "band_AOT": granule / "R10m" / str(band_path + "AOT_10m.jp2"),
            "band_02": granule / "/R10m/" / str(band_path + "B02_10m.jp2"),
            "band_03": granule / "/R10m/" / str(band_path + "B03_10m.jp2"),
            "band_04": granule / "/R10m/" / str(band_path + "B04_10m.jp2"),
            "band_05": granule / "/R20m/" / str(band_path + "B05_20m.jp2"),
            "band_06": granule / "/R20m/" / str(band_path + "B06_20m.jp2"),
            "band_07": granule / "/R20m/" / str(band_path + "B07_20m.jp2"),
            "band_08": granule / "/R10m/" / str(band_path + "B08_10m.jp2"),
            "band_8A": granule / "/R20m/" / str(band_path + "B8A_20m.jp2"),
            "band_09": granule / "/R60m/" / str(band_path + "B09_60m.jp2"),
            "band_WVP": granule / "/R10m/"/ str(band_path + "WVP_10m.jp2"),
            "band_11": granule / "/R20m/" / str(band_path + "B11_20m.jp2"),
            "band_12": granule / "/R20m/" / str(band_path + "B12_20m.jp2"),
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
        # sys.exit()

        gdal.Translate(geotiff_output, vrt_dataset, format="GTiff")


        return geotiff_output
