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

# TODO suppport for mosaicing within same orbital strip
# metadata now follow all the way to output, see splitter for xml tag.
# TODO Use Vandportalen.dk to determine flood timing going forward
# TODO quality checker in wrapper. Dont bother with dynamic range.
# TODO file cleanup after successful job
#   subsequentlý a working dir doesnt need to be specified maybe?
# TODO Support for both sigma0 and gamma0 in same dataset
# TODO Trimmer module called on sentinel 1 and 2 in wrapper
# TODO toolprinter
# TODO split all these tasks up as issues in git?
# TODO update readme
# TODO rename pre_process_graph to snap_graph
# TODO double check max cloud in download vs aoi. Seperate vars?

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

# for multiple tasks, loop over a list of lists and unpack working dir, crs, shape and date
pre_processor = PreProcessor(
    threads = 1,
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
