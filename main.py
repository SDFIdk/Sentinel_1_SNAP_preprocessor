from pre_process_manager import PreProcessor

#CDSE constants
concurrency = 4     #CDSE allows for max 4 concurrencies unless you got a special account

#Sentinel-1 constants
threads = 1
gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe'
pre_process_graph = 'snap_graphs/preprocessing_workflow_2023_no_cal_incidence.xml'



#Sentinel-2 constants




#User inputs
working_dir = 'some_dir/'
crs = 'EPSG:25832' 
shape = 'ribe_aoi/ribe_aoi.shp'
date_range = ''



#script calls a coordinator function which launches the different scripts



pre_processor = PreProcessor(crs)

pre_processor.start_workflow()