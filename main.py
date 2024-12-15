from pre_process_manager import PreProcessor
from osgeo import gdal  # for some reason it crashes if imported in other modules????

# #CDSE constants
# concurrency = 4     #CDSE allows for max 4 concurrencies unless you got a special account

# #Sentinel-1 constants
# threads = 1
# gpt_exe = 'C:/Users/b025527/AppData/Local/snap/bin/gpt.exe' #remote pc
# polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid
# land_polygon = "shapes/landpolygon_1000.zip"

# #Sentinel-2 constants
# max_cloud_pct = 40 #Fraction agreed upon with GEUS
# max_empty = 80

# TODO Use Vandportalen.dk to determine flood timing going forward
# TODO Support for both sigma0 and gamma0 in same dataset
# TODO logger
# TODO harden the acquisistion against bad data until CDSETool is patched
# TODO inhertaince based class system for S2 component

# User inputs
working_dir = "TEST_DATA_FULL_SEND2"
crs = "EPSG:25832"
shape = "shapes/holstebro/POLYGON.shp"
start_date = "2015-11-20"
end_date = "2015-11-25"
pre_process_graph = (
    "sentinel_1/snap_graphs/preprocessing_workflow_2023_incidence_geotiff.xml"
)
result_dir = "results/"

pre_processor = PreProcessor(
    # threads=1,
    working_dir=working_dir,
    shape=shape,
    start_date=start_date,
    end_date=end_date,
    pre_process_graph=pre_process_graph,
    result_dir=result_dir,
)

pre_processor.start_workflow()