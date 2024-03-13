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
# TODO quality checker in wrapper.
# TODO Support for both sigma0 and gamma0 in same dataset
# TODO logger
# TODO write resolution, denoise_mode and unit to metadata to simplify "sort_unit" inputs.
# TODO ensure functions preserve metadata 65000. Possibly create a setup and teardown for that? If that goes for individual files.
# TODO harden the acquisistion against bad data until CDSETool is patched

# User inputs
working_dir = "TEST_DATA_FULL_SEND"
crs = "EPSG:25832"
shape = "shapes/stavis_odense/POLYGON.shp"
start_date = "2024-02-05"
end_date = "2024-02-13"
pre_process_graph = (
    "sentinel_1/snap_graphs/preprocessing_workflow_2023_incidence_geotiff.xml"
)
result_dir = "results/"

pre_processor = PreProcessor(
    threads=1,
    working_dir=working_dir,
    crs=crs,
    shape=shape,
    start_date=start_date,
    end_date=end_date,
    pre_process_graph=pre_process_graph,
    denoise_mode="mean",
    result_dir=result_dir,
)

pre_processor.start_workflow()