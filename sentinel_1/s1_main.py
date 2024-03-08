import sys
import os
from pathlib import Path
from sentinel_1.denoiser import Denoiser
from sentinel_1.snap_converter import SnapPreprocessor
from sentinel_1.tool_manager import ToolManager

from sentinel_1.tools.align_raster import AlignRaster
from sentinel_1.tools.change_resolution import ChangeResolution
from sentinel_1.tools.clip_256 import Clip256
from sentinel_1.tools.convert_unit import ConvertUnit
from sentinel_1.tools.copy_dir import CopyDir
from sentinel_1.tools.land_sea_mask import LandSeaMask
from sentinel_1.tools.remove_empty import RemoveEmpty
from sentinel_1.tools.sort_output import SortOutput
from sentinel_1.tools.split_polarizations import SplitPolarizations
from sentinel_1.tools.trim_256 import Trim256

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
        self.denoise_modes = kwargs.get("denoise_mode", ["SAR2SAR"])
        if not isinstance(self.denoise_modes, list):
            self.denoise_modes = [self.denoise_modes]
        self.polarization = kwargs.get("polarization", ["VV", "VH"])
        self.land_polygon = kwargs.get("land_polygon", "shapes/landpolygon_1000.zip")

        Path(self.geotiff_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sentinel_1_output).mkdir(parents=True, exist_ok=True)

        if not isinstance(self.polarization, list):
            self.polarization = [self.polarization]
        if not isinstance(self.polarization, list):
            self.denoise_modes = [self.denoise_modes]

    def s1_workflow(self):
        geotiff_utils = ToolManager(
            self.geotiff_dir, "*.tif", threads=self.threads, polarization=self.polarization
        )
        snap_executor = SnapPreprocessor(gpt_path=self.gpt_exe)
        denoiser = Denoiser(self.geotiff_dir, self.shape)

        snap_executor.graph_processing(
            self.safe_dir, self.geotiff_dir, self.pre_process_graph, input_ext=".zip"
        )

        copy_dir = os.path.join(self.working_dir, "geotiff_copy")

        geotiff_utils.util_starter("copy_dir", copy_dir=copy_dir)
        # copy_dir_utils = ToolManager(
        #     copy_dir, "*.tif", threads=1, polarization=self.polarization
        # )

        SplitPolarizations(self.geotiff_dir, self.shape, self.polarization, self.crs).run()
        geotiff_utils.util_starter(
            "split_polarizations",
            output_dir=self.geotiff_dir,
            shape=self.shape,
            crs=self.crs,
        )

        AlignRaster(input_dir = self.geotiff_dir).run()

        LandSeaMask(self.geotiff_dir, self.land_polygon).run()

        RemoveEmpty(self.geotiff_dir)

        for i, denoise_mode in enumerate(self.denoise_modes):
            resolution = 10
            # if not i == 0: copy_dir_utils.util_starter("copy_dir", copy_dir=self.geotiff_dir)

            denoiser.select_denoiser(denoise_mode, to_intensity=False)

            ChangeResolution(self.geotiff_dir, resolution).run()
            ConvertUnit(self.geotiff_dir, "linear", "decibel").run()
            AlignRaster(input_dir = self.geotiff_dir).run()
            Trim256(self.geotiff_dir).run()
            SortOutput(self.geotiff_dir, self.sentinel_1_output, denoise_mode, "decibel", resolution, self.polarization).run()

            ConvertUnit(self.geotiff_dir, "decibel", "power").run()
            AlignRaster(input_dir = self.geotiff_dir).run()
            Trim256(self.geotiff_dir).run()
            SortOutput(self.geotiff_dir, self.sentinel_1_output, denoise_mode, "power", resolution, self.polarization).run()