import sys
import os
from osgeo import gdal  # for some reason it crashes if imported in other modules????
from pathlib import Path

if __name__ == "__main__":
    from denoiser import Denoiser
    from snap_converter import SnapPreprocessor
    from tool_manager import ToolManager
    from s1_main import S1Preprocessor

    working_dir = "D:/working_dir/ribe_2024_01_22/"
    shape = "ribe_aoi/ribe_aoi.shp"

    netcdf_dir = working_dir + "netcdf/"
    geotiff_dir = working_dir + "geotiff_dir/"

    pre_process_graph = "snap_graphs/preprocessing_workflow_2023_no_cal_incidence.xml"
    gpt_exe = "C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe"
    crs = "EPSG:25832"
    polarization = ["VV", "VH"]

    s1_preprocessor = S1Preprocessor(
        working_dir=working_dir,
        netcdf_dir=netcdf_dir,
        geotiff_dir=geotiff_dir,
        shape=shape,
        pre_process_graph=pre_process_graph,
        gpt_exe=gpt_exe,
        crs=crs,
        polarization=polarization,
    )
    s1_preprocessor.s1_workflow()
else:
    from sentinel_1.denoiser import Denoiser
    from sentinel_1.snap_converter import SnapPreprocessor
    from sentinel_1.tool_manager import ToolManager


class S1Preprocessor:
    @property
    def safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_1", "safe")

    @property
    def netcdf_dir(self):
        return os.path.join(self.working_dir, "sentinel_1", "netcdf")

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

        Path(self.netcdf_dir).mkdir(parents=True, exist_ok=True)
        Path(self.geotiff_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sentinel_1_output).mkdir(parents=True, exist_ok=True)

        if not isinstance(self.polarization, list):
            self.polarization = [self.polarization]
        if not isinstance(self.polarization, list):
            self.denoise_modes = [self.denoise_modes]

    def s1_workflow(self):
        # safe_utils = ToolManager(safe_dir, '*.zip', 1)
        netcdf_utils = ToolManager(
            self.netcdf_dir, "*.nc", threads=1, polarization=self.polarization
        )
        geotiff_utils = ToolManager(
            self.geotiff_dir, "*.tif", threads=1, polarization=self.polarization
        )
        snap_executor = SnapPreprocessor(gpt_path=self.gpt_exe)
        denoiser = Denoiser(self.geotiff_dir, self.shape)

        snap_executor.graph_processing(
            self.safe_dir, self.netcdf_dir, self.pre_process_graph, input_ext=".zip"
        )

        netcdf_utils.util_starter("netcdf_to_geotiff", output_dir=self.geotiff_dir)
        geotiff_utils.util_starter("clip_256", shape=self.shape, crs=self.crs)

        copy_dir = os.path.join(self.working_dir, "non_denoised")
        geotiff_utils.util_starter("copy_dir", copy_dir=copy_dir)
        copy_dir_utils = ToolManager(
            copy_dir, "*.tif", threads=1, polarization=self.polarization
        )

        for i, denoise_mode in enumerate(self.denoise_modes):
            resolution = 10
            if not i == 0:
                copy_dir_utils.util_starter("copy_dir", copy_dir=self.geotiff_dir)

            denoiser.select_denoiser(denoise_mode, to_intensity=False)

            geotiff_utils.util_starter("change_resolution", x_size=resolution)
            geotiff_utils.util_starter(
                "convert_unit", source_unit="linear", destination_unit="decibel"
            )
            geotiff_utils.util_starter("align_raster")
            geotiff_utils.util_starter(
                "sort_output",
                output=self.sentinel_1_output,
                working_dir=self.working_dir,
                denoise_mode=denoise_mode,
                unit="decibel",
                resolution=resolution,
            )

            geotiff_utils.util_starter(
                "convert_unit", source_unit="decibel", destination_unit="power"
            )
            geotiff_utils.util_starter("align_raster")
            geotiff_utils.util_starter(
                "sort_output",
                output=self.sentinel_1_output,
                working_dir=self.working_dir,
                denoise_mode=denoise_mode,
                unit="power",
                resolution=resolution,
            )

            resolution = 20

            geotiff_utils.util_starter(
                "convert_unit", source_unit="power", destination_unit="linear"
            )
            geotiff_utils.util_starter("change_resolution", x_size=resolution)

            geotiff_utils.util_starter(
                "convert_unit", source_unit="linear", destination_unit="decibel"
            )
            geotiff_utils.util_starter("align_raster")
            geotiff_utils.util_starter(
                "sort_output",
                output=self.sentinel_1_output,
                working_dir=self.working_dir,
                denoise_mode=denoise_mode,
                unit="decibel",
                resolution=resolution,
            )

            geotiff_utils.util_starter(
                "convert_unit", source_unit="decibel", destination_unit="power"
            )
            geotiff_utils.util_starter("align_raster")
            geotiff_utils.util_starter(
                "sort_output",
                output=self.sentinel_1_output,
                working_dir=self.working_dir,
                denoise_mode=denoise_mode,
                unit="power",
                resolution=resolution,
            )
