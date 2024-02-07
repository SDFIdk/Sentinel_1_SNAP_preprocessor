import sys
from osgeo import gdal  # for some reason it crashes if imported in other modules????

from clip_256 import Clipper
from tool_manager import Tool_manager
import unit_converter

if __name__ == "__main__":
    import glob

    geotiff_dir = "D:/geus_transfer_january/"

geotiff_files = glob.glob(geotiff_dir + "**/*.tif", recursive=True)

decibel_files = []
power_files = []
for geotiff in geotiff_files:
    if "decibel" in geotiff:
        decibel_files.append(geotiff)
    elif "power_transform" in geotiff:
        power_files.append(geotiff)
    else:
        print(geotiff)


# geotiff_files = glob.glob(geotiff_dir + '**/*.tif', recursive=True)
# Tool_manager.util_starter('trimmer_256', 1, {
#         'input_dir':geotiff_files,
#         })

unit_converter.convert_unit(power_files, "linear", "power")
unit_converter.convert_unit(decibel_files, "linear", "decibel")

Tool_manager.util_starter('remove_empty', 1, {
        'input_dir':geotiff_files,
        })