from cdse_downloader.downloader import Downloader
from s1.s1_main import S1Preprocessor

import os

class PreProcessor:

    def __init__(self, **kwargs):

        working_dir = kwargs['working_dir']
        kwargs['safe_dir'] = working_dir + 'safe/'
        kwargs['netcdf_dir'] = working_dir + 'netcdf/'
        kwargs['geotiff_dir'] = working_dir + 'geotiff/'
        os.mkdir(kwargs['working_dir'])
        os.mkdir(kwargs['safe_dir'])
        os.mkdir(kwargs['netcdf'])
        os.mkdir(kwargs['geotiff'])
        
        self.downloader = Downloader(**kwargs)
        self.s1_preprocessor = S1Preprocessor(**kwargs)
        #add other constants

    def start_workflow(self):

        self.downloader.download_sentinel_2()




        