import os
import sys
from pathlib import Path

from sentinel_2.s2_preprocessing import Preprocessor


class S2Preprocessor:
    @property
    def safe_dir(self):
        # return os.path.join(self.working_dir, "sentinel_2", "safe")

        #TEMPORARY WORKAROUND
        return os.path.join("sentinel_2_temp_dir/", "sentinel_2", "geotiff") 

    @property
    def geotiff_dir(self):
        # return os.path.join(self.working_dir, "sentinel_2", "geotiff")

        #TEMPORARY WORKAROUND
        return os.path.join("sentinel_2_temp_dir/", "sentinel_2", "geotiff") 

    @property
    def sentinel_2_output(self):
        return os.path.join(self.result_dir, "sentinel_2")

    def __init__(self, **kwargs):
        self.working_dir = kwargs["working_dir"]
        self.crs = kwargs["crs"]
        self.shape = kwargs["shape"]
        self.max_cloud_pct = kwargs.get("max_cloud_pct", 40)
        self.max_empty = kwargs.get("max_empty", 80)
        self.result_dir = kwargs["result_dir"]

        Path(self.safe_dir).mkdir(parents=True, exist_ok=True)
        Path(self.geotiff_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sentinel_2_output).mkdir(parents=True, exist_ok=True)

    def s2_workflow(self):
        preprocessor = Preprocessor(self.safe_dir, self.geotiff_dir)

        preprocessor.self_check(self.crs)

        preprocessor.s2_safe_to_geotiff(self.max_cloud_pct, self.shape)

        preprocessor.warp_files_to_crs(self.crs)

        preprocessor.clip_to_shape(self.shape, self.crs)

        preprocessor.warp_files_to_crs(self.crs)

        preprocessor.remove_empty_files(self.max_empty)

        preprocessor.result_mover(self.geotiff_dir, self.sentinel_2_output)
