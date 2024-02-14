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

    def generate_geotiffs(inputProductPath, outputPath):
        basename = os.path.basename(inputProductPath)
        safe_dir = outputPath + basename[:-3] + "SAFE"
        if os.path.isdir(safe_dir):
            pass
        else:
            zip = zipfile.ZipFile(inputProductPath)
            zip.extractall(outputPath)

        directoryName = safe_dir + "/GRANULE"

        productName = os.path.basename(inputProductPath)[:-4]
        outputPathSubdirectory = outputPath + productName + "_PROCESSED"

        if not os.path.exists(outputPathSubdirectory):
            os.makedirs(outputPathSubdirectory)

        if not os.path.exists(outputPathSubdirectory):
            os.makedirs(outputPathSubdirectory)

        subDirectories = Tiff_generator.get_immediate_subdirectories(directoryName)
        results = []
        for granule in subDirectories:
            unprocessedBandPath = (
                outputPath
                + productName
                + ".SAFE/GRANULE/"
                + granule
                + "/"
                + "IMG_DATA/"
            )
            results.append(
                Tiff_generator.generate_all_bands(
                    unprocessedBandPath, granule, outputPathSubdirectory, outputPath
                )
            )

        shutil.rmtree(safe_dir)
        shutil.rmtree(outputPathSubdirectory)

    def generate_all_bands(
        unprocessedBandPath, granule, outputPathSubdirectory, newout
    ):
        granuleBandTemplate = granule[:-6]
        granpart_1 = unprocessedBandPath.split(".SAFE")[0][-22:-16]
        granule_2 = unprocessedBandPath.split(".SAFE")[0][-49:-34]

        granuleBandTemplate = granpart_1 + "_" + granule_2 + "_"

        outputPathSubdirectory = outputPathSubdirectory
        if not os.path.exists(outputPathSubdirectory + "/IMAGE_DATA"):
            os.makedirs(outputPathSubdirectory + "/IMAGE_DATA")

        outPutTiff = "/" + granule[:-6] + "16Bit-AllBands.tif"
        outPutVRT = "/" + granule[:-6] + "16Bit-AllBands.vrt"

        outPutFullPath = newout + outPutTiff
        outPutFullVrt = outputPathSubdirectory + "/IMAGE_DATA/" + outPutVRT
        inputPath = unprocessedBandPath

        bands = {
            "band_AOT": inputPath + "R10m/" + granuleBandTemplate + "AOT_10m.jp2",
            "band_02": inputPath + "R10m/" + granuleBandTemplate + "B02_10m.jp2",
            "band_03": inputPath + "R10m/" + granuleBandTemplate + "B03_10m.jp2",
            "band_04": inputPath + "R10m/" + granuleBandTemplate + "B04_10m.jp2",
            "band_05": inputPath + "R20m/" + granuleBandTemplate + "B05_20m.jp2",
            "band_06": inputPath + "R20m/" + granuleBandTemplate + "B06_20m.jp2",
            "band_07": inputPath + "R20m/" + granuleBandTemplate + "B07_20m.jp2",
            "band_08": inputPath + "R10m/" + granuleBandTemplate + "B08_10m.jp2",
            "band_8A": inputPath + "R20m/" + granuleBandTemplate + "B8A_20m.jp2",
            "band_09": inputPath + "R60m/" + granuleBandTemplate + "B09_60m.jp2",
            "band_WVP": inputPath + "R10m/" + granuleBandTemplate + "WVP_10m.jp2",
            "band_11": inputPath + "R20m/" + granuleBandTemplate + "B11_20m.jp2",
            "band_12": inputPath + "R20m/" + granuleBandTemplate + "B12_20m.jp2",
        }

        vrt_dataset = gdal.BuildVRT(
            outPutFullVrt,
            list(bands.values()),
            separate=True,
            resolution="user",
            xRes=20,
            yRes=20,
        )

        for i, band_name in enumerate(bands, start=1):
            band = vrt_dataset.GetRasterBand(i)
            band.SetMetadataItem("DESCRIPTION", band_name)

        gdal.Translate(outPutFullPath, vrt_dataset, format="GTiff")

        return outPutFullPath
