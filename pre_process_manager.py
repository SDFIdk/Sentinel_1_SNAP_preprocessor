from cdse_downloader.downloader import Downloader
from sentinel_1.s1_main import S1Preprocessor
from sentinel_2.s2_main import S2Preprocessor
from result_wrapper.wrapper import ResultWrapper
from pathlib import Path

import sys

class PreProcessor:
    def __init__(self, **kwargs):
        Path(kwargs["working_dir"]).mkdir(parents=True, exist_ok=True)

        self.downloader = Downloader(**kwargs)
        self.s1_preprocessor = S1Preprocessor(**kwargs)
        self.s2_preprocessor = S2Preprocessor(**kwargs)
        self.wrapper = ResultWrapper(**kwargs)

    def start_workflow(self):
        # self.downloader.download_sentinel_1()
        # self.s1_preprocessor.s1_workflow()

        # self.downloader.download_sentinel_2()
        # self.s2_preprocessor.s2_workflow()

        self.wrapper.wrap_results()

        print('## Dataset completed!')