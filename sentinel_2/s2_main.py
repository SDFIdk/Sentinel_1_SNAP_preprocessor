import os
from pathlib import Path

from sentinel_2.tools.safe_to_geotiff import SAFEToGeotiff
from sentinel_2.tools.warp_to_crs import CRSWarp
from sentinel_2.tools.clip_to_shape import ClipToShape
from sentinel_2.tools.remove_empty import RemoveEmpty
from sentinel_2.tools.result_mover import ResultMover

class S2Preprocessor:
    @property
    def safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_2", "safe")

    @property
    def geotiff_dir(self):
        return os.path.join(self.working_dir, "sentinel_2", "geotiff")

    @property
    def sentinel_2_output(self):
        return os.path.join(self.result_dir, "sentinel_2")

    def __init__(self, **kwargs):
        self.working_dir = kwargs["working_dir"]
        self.crs = kwargs.get("crs", "EPSG:25832")
        self.shape = kwargs.get("shape", None)
        self.max_cloud = kwargs.get("max_cloud_pct", 40)
        self.max_empty = kwargs.get("max_empty", 80)
        self.result_dir = kwargs["result_dir"]
        self.clip_to_shape = kwargs.get("clip_to_shape", True)

        Path(self.safe_dir).mkdir(parents=True, exist_ok=True)
        Path(self.geotiff_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sentinel_2_output).mkdir(parents=True, exist_ok=True)

    def s2_workflow(self):
        
        SAFEToGeotiff(self.safe_dir, self.geotiff_dir, self.max_cloud, shape = self.shape).run()
        if self.clip_to_shape: ClipToShape(self.geotiff_dir, self.shape, self.crs)
        RemoveEmpty(self.max_empty)
        CRSWarp(self.geotiff_dir, self.crs).run()
        ResultMover(self.geotiff_dir, self.sentinel_2_output).run()
