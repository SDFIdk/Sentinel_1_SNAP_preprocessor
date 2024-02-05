import sys
from osgeo import gdal  #for some reason it crashes if imported in other modules????

from clip_256 import Clipper
from tool_manager import Tool_manager

if __name__== '__main__':
    import glob
    geotiff_dir = 'D:/geus_transfer_january/'

geotiff_files = glob.glob(geotiff_dir + '**/*.tif', recursive=True)
# Tool_manager.util_starter('remove_empty', 1, {
#         'input_dir':geotiff_files,
#         })

geotiff_files = glob.glob(geotiff_dir + '**/*.tif', recursive=True)
Tool_manager.util_starter('trimmer_256', 1, {
        'input_dir':geotiff_files,
        })