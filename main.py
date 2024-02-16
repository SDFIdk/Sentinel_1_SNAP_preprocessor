from pre_process_manager import PreProcessor
from osgeo import gdal  # for some reason it crashes if imported in other modules????

# #CDSE constants
# concurrency = 4     #CDSE allows for max 4 concurrencies unless you got a special account

# #Sentinel-1 constants
# threads = 1   
# gpt_exe =           
# polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid

# #Sentinel-2 constantspytho
# max_cloud_pct = 40
# max_empty = 80


# User inputs
working_dir = "input/"
crs = "EPSG:25832"
shape = "shapes/stavis_odense/POLYGON.shp"
start_date = '2024-02-09'
end_date = '2024-02-13'
pre_process_graph = 'sentinel_1/snap_graphs/preprocessing_workflow_2023_no_cal_incidence.xml'
result_dir = "results/"

# for multiple tasks, loop over a list of lists and unpack working dir, crs, shape and date
pre_processor = PreProcessor(
    working_dir=working_dir,
    crs=crs,
    shape=shape,
    start_date = start_date,
    end_date = end_date,
    pre_process_graph = pre_process_graph,
    denoise_mode = 'mean',
    max_cloud_pct = 100,
    result_dir = result_dir
)

pre_processor.start_workflow()
