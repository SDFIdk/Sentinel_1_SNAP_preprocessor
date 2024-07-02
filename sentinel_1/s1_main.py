import sys
import os
from pathlib import Path
from sentinel_1.tools.denoiser import Denoiser

from sentinel_1.tools.snap_executor import SnapExecutor
from sentinel_1.tools.align_raster import AlignRaster
from sentinel_1.tools.change_resolution import ChangeResolution
from sentinel_1.tools.convert_unit import ConvertUnit
from sentinel_1.tools.land_sea_mask import LandSeaMask
from sentinel_1.tools.remove_empty import RemoveEmpty
from sentinel_1.tools.sort_output import SortOutput
from sentinel_1.tools.split_polarizations import SplitPolarizations
from sentinel_1.tools.trim_256 import Trim256
from sentinel_1.tools.clip_256 import Clip256
from sentinel_1.tools.mosaic_orbits import MosaicOrbits
from sentinel_1.tools.build_pyramids import BuildPyramids
from sentinel_1.tools.copy_dir import CopyDir
from sentinel_1.tools.denoiser import Denoiser

class S1Preprocessor:
    @property
    def safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_1", "safe")

    @property
    def geotiff_dir(self):
        return os.path.join(self.working_dir, "sentinel_1", "geotiff")

    @property
    def sentinel_1_output(self):
        return os.path.join(self.result_dir, "sentinel_1")

    def __init__(self, **kwargs):
        self.working_dir = kwargs["working_dir"]
        self.crs = kwargs["crs"]
        self.shape = kwargs["shape"]
        self.pre_process_graph = kwargs["pre_process_graph"]
        self.result_dir = kwargs["result_dir"]
        self.gpt_exe = kwargs.get(
            "gpt_exe", "C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe"
        )
        self.threads = kwargs.get("threads", 1)
        self.land_polygon = kwargs.get("land_polygon", "shapes/landpolygon_1000.zip")
        self.mosaic_orbits = kwargs.get("mosaic_orbits", False)
        self.clip_to_shape = kwargs.get("clip_to_shape", True)
        self.resolution = kwargs.get("resolution", 10)

        Path(self.geotiff_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sentinel_1_output).mkdir(parents=True, exist_ok=True)

        self.polarization = kwargs.get("polarization", ["VV", "VH"])
        if not isinstance(self.polarization, list):
            self.polarization = [self.polarization]

    def s1_workflow(self):

        SnapExecutor(self.safe_dir, self.geotiff_dir, self.gpt_exe, self.pre_process_graph, threads = 6).run()
        
        if self.mosaic_orbits: 
            MosaicOrbits(self.geotiff_dir).run()

        if self.clip_to_shape:
            Clip256(self.geotiff_dir).run()
            RemoveEmpty(self.geotiff_dir)

        SplitPolarizations(
            input_dir= self.geotiff_dir, 
            shape = self.shape, 
            polarization = self.polarization, 
            crs = self.crs,
        ).run()

        BuildPyramids(self.geotiff_dir).run()
        CopyDir(self.geotiff_dir, "J:/javej/geus_total_rerun/whole_dk_mosaic/sentinel_1/bu_split")

        LandSeaMask(self.geotiff_dir, self.land_polygon).run()
        RemoveEmpty(self.geotiff_dir)
        Denoiser(self.geotiff_dir).run()
        ChangeResolution(self.geotiff_dir, self.resolution).run()

        ConvertUnit(self.geotiff_dir, "linear", "decibel").run()
        AlignRaster(input_dir=self.geotiff_dir).run()
        Trim256(self.geotiff_dir).run()
        BuildPyramids(self.geotiff_dir).run()
        SortOutput(
            self.geotiff_dir,
            self.sentinel_1_output,
            "decibel",
            self.resolution,
            self.polarization,
        ).run()

        ConvertUnit(self.geotiff_dir, "decibel", "power").run()
        AlignRaster(input_dir=self.geotiff_dir).run()
        Trim256(self.geotiff_dir).run()
        BuildPyramids(self.geotiff_dir).run()
        SortOutput(
            self.geotiff_dir,
            self.sentinel_1_output,
            "power",
            self.resolution,
            self.polarization,
        ).run()
