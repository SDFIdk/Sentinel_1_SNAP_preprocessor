from sentinel_2.s2_preprocessing import Preprocessor

import os
import sys
from pathlib import Path


# if __name__ == "__main__":
#     from sentinel_2.s2_main import S2Preprocessor
#     working_dir = "input/"

#     shape = "shapes/sneum_aa/layers/POLYGON.shp"
#     crs = "EPSG:25832"
#     max_cloud_pct = 40  # max allowed cloud pct in aoi
#     max_empty = 80  # Removes files with too much noData

#     s2_preprocessor = S2Preprocessor(
#         working_dir=working_dir,
#         crs=crs,
#         shape=shape,
#         max_cloud_pct=max_cloud_pct,
#         max_empty=max_empty,
#     )

#     s2_preprocessor.s2_workflow()


class S2Preprocessor:
    @property
    def safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_2", "safe")

    @property
    def geotiff_dir(self):
        return os.path.join(self.working_dir, "sentinel_2", "geotiff")

    def __init__(self, **kwargs):
        self.working_dir = kwargs["working_dir"]
        self.crs = kwargs["crs"]
        self.shape = kwargs["shape"]
        self.max_cloud_pct = kwargs.get("max_cloud_pct", 40)
        self.max_empty = kwargs.get("max_empty", 80)

        Path(self.safe_dir).mkdir(parents=True, exist_ok=True)
        Path(self.geotiff_dir).mkdir(parents=True, exist_ok=True)

    def s2_workflow(self):
        preprocessor = Preprocessor(self.safe_dir, self.geotiff_dir)

        preprocessor.self_check(self.crs)

        preprocessor.s2_safe_to_geotiff(self.max_cloud_pct, self.shape)

        preprocessor.warp_files_to_crs(self.crs)

        preprocessor.clip_to_shape(self.shape, self.crs)

        preprocessor.warp_files_to_crs(self.crs)

        preprocessor.remove_empty_files(self.max_empty)