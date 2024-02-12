import os
import sys

from s2.s2_preprocessing import Preprocessor

if __name__== '__main__':

    # input_dir = 'input/'
    # input_dir = "input/ribe/"
    # input_dir = "input/skjern/"
    # input_dir = "input/varde/"
    input_dir = "input/sneum_aa/"

    # output_dir = "output/ribe_2024_22_01/"
    # output_dir = "output/skjern_2024_22_01/"
    # output_dir = "output/varde_2024_22_01/"
    output_dir = "output/sneum_aa_2024_22_01/"

    # output_dir = 'output/holstebro_2022_12_31/'
    # input/output will be created if not present

    # shape = 'ribe_aoi/ribe_aoi.shp'
    # shape = "shapes/skjern/layers/POLYGON.shp"
    # shape = "shapes/varde/layers/POLYGON.shp"
    shape = "shapes/sneum_aa/layers/POLYGON.shp"

    # path to .shp file in unzipped shape dir

    crs = 'EPSG:25832'
    # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 

    max_cloud_pct = 40  #max allowed cloud pct in aoi
    # Note this range extends to whole raster, not shape extent

    max_empty = 80  #Removes files with too much noData


preprocessor = Preprocessor(input_dir, output_dir)

preprocessor.self_check(crs)

preprocessor.s2_safe_to_geotiff(max_cloud_pct, shape)

preprocessor.warp_files_to_crs(crs)  

preprocessor.clip_to_shape(shape, crs)      

preprocessor.warp_files_to_crs(crs)       

preprocessor.remove_empty_files(max_empty_percent = max_empty)