import os
import shutil
import glob
from pathlib import Path
from osgeo import gdal
import shutil

from sentinel_2.s2_utils import Utils

gdal.UseExceptions()
gdal.PushErrorHandler(Utils.gdal_error_handler)

class TiffGenerator(object):
    def complete(text, state):
        return (glob.glob(text + "*") + [None])[state]

    def generate_geotiffs(safe_file, geotiff_output_path):

        safe_unzip_dir = os.path.join(geotiff_output_path, os.path.basename(safe_file)[:-4] + ".SAFE")

        Utils.unzip_data_to_dir(safe_file, geotiff_output_path, direct = True)

        product_name = os.path.basename(safe_file).replace(".zip", "_PROCESSED")
        output_subdirectory = os.path.join(geotiff_output_path, product_name)
        Path(output_subdirectory).mkdir(exist_ok=True)

        sub_directories = Utils.get_immediate_subdirectories(
            safe_unzip_dir + "/GRANULE"
        )

        for granule in sub_directories:
            unprocessed_band = os.path.join(
                geotiff_output_path, product_name + ".SAFE", "GRANULE", granule, "IMG_DATA"
            )
            TiffGenerator.generate_all_bands(
                unprocessed_band, granule, output_subdirectory, geotiff_output_path
            )

        shutil.rmtree(safe_unzip_dir)
        shutil.rmtree(output_subdirectory)

        os.remove(safe_file)    #somehow necessary


    def generate_all_bands(unprocessed_band, granule, output_subdirectory, newout):
        granule_part_1 = unprocessed_band.split(".SAFE")[0][-22:-16]
        granule_part_2 = unprocessed_band.split(".SAFE")[0][-49:-34]    # Hardcoded for standard Sentinel-2 band names 
        band_path = granule_part_1 + "_" + granule_part_2 + "_"

        if not os.path.exists(output_subdirectory + "/IMAGE_DATA"):
            os.makedirs(output_subdirectory + "/IMAGE_DATA")

        output_tiff = "/" + granule[:-6] + "16Bit-AllBands.tif"
        output_vrt = "/" + granule[:-6] + "16Bit-AllBands.vrt"

        geotiff_output = newout + output_tiff
        output_vrt = output_subdirectory + "/IMAGE_DATA/" + output_vrt
        granule = Path(unprocessed_band)

        bands = {
            "band_AOT": str(granule / "R10m" / str(band_path + "AOT_10m.jp2")),
            "band_02": str(granule / "R10m" / str(band_path + "B02_10m.jp2")),
            "band_03": str(granule / "R10m" / str(band_path + "B03_10m.jp2")),
            "band_04": str(granule / "R10m" / str(band_path + "B04_10m.jp2")),
            "band_05": str(granule / "R20m" / str(band_path + "B05_20m.jp2")),
            "band_06": str(granule / "R20m" / str(band_path + "B06_20m.jp2")),
            "band_07": str(granule / "R20m" / str(band_path + "B07_20m.jp2")),
            "band_08": str(granule / "R10m" / str(band_path + "B08_10m.jp2")),
            "band_8A": str(granule / "R20m" / str(band_path + "B8A_20m.jp2")),
            "band_09": str(granule / "R60m" / str(band_path + "B09_60m.jp2")),
            "band_WVP": str(granule / "R10m" / str(band_path + "WVP_10m.jp2")),
            "band_11": str(granule / "R20m" / str(band_path + "B11_20m.jp2")),
            "band_12": str(granule / "R20m" / str(band_path + "B12_20m.jp2")),
        }

        vrt_dataset = gdal.BuildVRT(
            output_vrt,
            list(bands.values()),
            separate=True,
            resolution="user",
            xRes=10,
            yRes=10,
        )

        for i, band_name in enumerate(bands, start=1):
            band = vrt_dataset.GetRasterBand(i)
            band.SetMetadataItem("DESCRIPTION", band_name)

        gdal.Translate(geotiff_output, vrt_dataset, format="GTiff")

        return geotiff_output
