from pre_process_manager import PreProcessor
from osgeo import gdal  # for some reason it crashes if imported in other modules????

# #CDSE constants
# concurrency = 4     #CDSE allows for max 4 concurrencies unless you have a special account

# #Sentinel-1 constants
# threads = 1
# gpt_exe = 'C:/Users/b025527/AppData/Local/snap/bin/gpt.exe' #remote pc
# polarization = ['VV', 'VH']     # list of strings or single string. For most sentinel-1 products, only VV, VH are valid
# land_polygon = "shapes/landpolygon_1000.zip"

# #Sentinel-2 constants
# max_cloud_pct = 40 #Fraction agreed upon with GEUS
# max_empty = 80

result_dir = "refactor_test"
pre_process_graph = "sentinel_1/snap_graphs/sigma0_incidence.xml"
# gpt_exe = 'C:/Users/b307579/AppData/Local/snap/bin/gpt.exe'
gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap10/bin/gpt.exe'
# gpt_exe = 'C:/Users/b025527/AppData/Local/snap/bin/gpt.exe'

location_list = [
    # ('J:/javej/geus_total_rerun/holstebro_2015/', "shapes/holstebro/POLYGON.shp", "2015-11-20", "2015-12-13"),
    # ('J:/javej/geus_total_rerun/holstebro_2022/', "shapes/holstebro/POLYGON.shp", "2022-12-18", "2023-01-13"),
    # ('J:/javej/geus_total_rerun/odense_2022/', "shapes/stavis_odense/POLYGON.shp", "2022-02-09", "2022-03-05"),
    # ('J:/javej/geus_total_rerun/ribe_2024/', "shapes/ribe/POLYGON.shp", "2024-01-11", "2024-01-25"),
    # ('J:/javej/geus_total_rerun/ribe_2020/', "shapes/ribe/POLYGON.shp", "2020-02-01", "2020-05-01"),
    # ('J:/javej/geus_total_rerun/skjern_2024/', "shapes/skjern/POLYGON.shp", "2024-01-11", "2024-01-25"),
    # ('J:/javej/geus_total_rerun/sneum_2024/', "shapes/sneum_aa/POLYGON.shp", "2024-01-11", "2024-01-25"),
    # ('J:/javej/geus_total_rerun/varde_2024/', "shapes/varde/POLYGON.shp", "2023-01-01", "2024-02-01"),

    # ('J:/javej/alling_aa_bst/', "shapes/alling_aa/POLYGON.shp", "2023-10-18", "2023-11-10"),

    ('refactor_test', "shapes/bornholm/POLYGON.shp", "2024-06-01", "2024-07-01"),
    ]

for location_data in location_list:
    working_dir, shape, start_date, end_date = location_data

    pre_processor = PreProcessor(
        threads = 1,
        working_dir="working_dir/" + working_dir,
        shape=shape,
        start_date=start_date,
        end_date=end_date,
        pre_process_graph=pre_process_graph,
        max_cloud_pct=80,
        result_dir='results/' + result_dir,
        gpt_exe=gpt_exe,
        # mosaic_orbits = True,
        clip_to_shape = True
    )
    pre_processor.start_workflow()