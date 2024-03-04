from osgeo import gdal
import sys
import os
from pathlib import Path
from sentinel_1.denoiser import Denoiser
from sentinel_1.snap_converter import SnapPreprocessor
from sentinel_1.tool_manager import ToolManager

from sentinel_1.tool_manager_inheritance import ToolManager as TESTMANAGER

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
        # snap_executor = SnapPreprocessor(gpt_path=self.gpt_exe)
        # denoiser = Denoiser(self.geotiff_dir, self.shape)

        # snap_executor.graph_processing(
        #     self.safe_dir, self.geotiff_dir, self.pre_process_graph, input_ext=".zip"
        # )

        # copy_dir = os.path.join(self.working_dir, "geotiff_copy")
        # geotiff_utils.util_starter("copy_dir", copy_dir=copy_dir)
        # copy_dir_utils = ToolManager(
        #     copy_dir, "*.tif", threads=1, polarization=self.polarization
        # )

        # geotiff_utils.util_starter(
        #     "split_polarizations",
        #     output_dir=self.geotiff_dir,
        #     shape=self.shape,
        #     crs=self.crs,
        # )

        TEST_utils = TESTMANAGER(
            self.geotiff_dir, "*.tif", threads=self.threads, polarization=self.polarization
        )
        geotiff_utils.util_starter("align_raster")
        sys.exit()

        geotiff_utils.util_starter("land_sea_mask", land_sea_mask = self.land_polygon)
        geotiff_utils.util_starter("remove_empty")

        for i, denoise_mode in enumerate(self.denoise_modes):
            resolution = 10
            if not i == 0: copy_dir_utils.util_starter("copy_dir", copy_dir=self.geotiff_dir)

            denoiser.select_denoiser(denoise_mode, to_intensity=False)

            geotiff_utils.util_starter("change_resolution", x_size=resolution)
            geotiff_utils.util_starter(
                "convert_unit", source_unit="linear", destination_unit="decibel"
            )
            geotiff_utils.util_starter("align_raster")
            geotiff_utils.util_starter("trimmer_256")
            geotiff_utils.util_starter(
                "sort_output",
                result_dir=self.sentinel_1_output,
                working_dir=self.working_dir,
                denoise_mode=denoise_mode,
                unit="decibel",
                resolution=resolution,
            )

            geotiff_utils.util_starter(
                "convert_unit", source_unit="decibel", destination_unit="power"
            )
            geotiff_utils.util_starter("align_raster")
            geotiff_utils.util_starter("trimmer_256")
            geotiff_utils.util_starter(
                "sort_output",
                result_dir=self.sentinel_1_output,
                working_dir=self.working_dir,
                denoise_mode=denoise_mode,
                unit="power",
                resolution=resolution,
            )
