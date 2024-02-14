import sys
from osgeo import gdal  # for some reason it crashes if imported in other modules????

from old_clip_256 import Clipper
from sentinel_1_tool_manager import ToolManager
import old_unit_converter

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

geotiff_utils = ToolManager(geotiff_files, "*.tif", threads=1)
geotiff_utils.util_starter("remove_empty")

power_utils = ToolManager(power_files, "*.tif", threads=1)
power_utils.util_starter("convert_unit", source_unit="linear", desitnation_unit="power")

decibel_utils = ToolManager(decibel_files, "*.tif", threads=1)
decibel_utils.util_starter(
    "convert_unit", source_unit="linear", desitnation_unit="decibel"
)
