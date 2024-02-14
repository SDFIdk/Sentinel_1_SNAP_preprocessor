import sys
import os
from multiprocessing.pool import Pool
from sentinel_1_utils import Utils
from old_clip_256 import Clipper


class OldToolManager:
    # def __init__(self, working_dir, tmp_dir):
    #     self.working_dir = working_dir
    #     self.tmp_dir = tmp_dir

    def self_check(crs, polarization, denoise_mode):
        # maybe this entire section shouldnt be here
        assert denoise_mode in [
            "SAR2SAR",
            "mean",
        ], f"## {denoise_mode} must match SAR2SAR or mean"
        assert Utils.is_valid_epsg(crs.replace("EPSG:", "")), "## CRS is not valid"
        assert polarization != None, (
            "## Polarization cannot be none"
            "## Polarization must be either VV, VH, HV or HH"
        )
        if not isinstance(polarization, list):
            polarization = [polarization]
        for pol in polarization:
            assert pol in [
                "VV",
                "VH",
                "HV",
                "HH",
            ], "## Polarization must be either VV, VH, HV or HH"
        return

    def util_starter(tool, threads, kwargs={}):
        if pre_init_dict.get(tool):
            kwargs = pre_init_dict.get(tool)(kwargs)

        if threads == 1:
            ToolManager.start_singleproc(tool, kwargs)
        elif threads > 1:
            print("fix multiproc. first!")
            ToolManager.start_singleproc(tool, kwargs)
            # Tool_manager.start_multiproc(tool, threads, kwargs)
        else:
            raise Exception(
                f"## Thread var must contain number greater than 0. Got {threads}"
            )

        # a "tool printer" would display a single printh the statement the tools previously provided

    def start_singleproc(tool, kwargs):
        input_dir = kwargs.get("input_dir")
        if isinstance(input_dir, list):
            input_file_list = input_dir
        else:
            input_file_list = Utils.file_list_from_dir(
                input_dir, ["*.tif", "*.nc", "*.zip"]
            )

        for i, input_file in enumerate(input_file_list):
            print("# " + str(i + 1) + " / " + str(len(input_file_list)), end="\r")

            kwargs["input_file"] = input_file
            tool_dict[tool](kwargs)

    def start_multiproc(self, tool, threads, kwargs):
        # items = []
        # for input_file in Utils.file_list_from_dir(kwargs.get('input_dir'), ['*.tif', '*.nc', '*.zip']):
        #     items.append((input_file, kwargs))

        # for result in Pool.starmap(tool_dict[tool], items):
        #     print() #?
        #     #also use that multiproc. thing that lets you specify threads.

        # with Pool(threads) as p:
        #     p.map(tool_dict[tool], (items))

        import concurrent.futures

        input_files = Utils.file_list_from_dir(
            kwargs.get("input_dir"), ["*.tif", "*.nc", "*.zip"]
        )

        def process_file(tool, input_file, **kwargs):
            return tool_dict[tool](input_file, **kwargs)

        with concurrent.futures.ProcessPoolExecutor(max_workers=threads) as executor:
            tasks = [
                executor.submit(process_file, tool, file, **kwargs)
                for file in input_files
            ]
            results = [task.result() for task in concurrent.futures.as_completed(tasks)]


tool_dict = {
    "split_geotiff": Utils.split_polarizations,
    "change_resolution": Utils.change_raster_resolution,
    "sort_output": Utils.sort_output,
    "align_raster": Utils.align_raster,
    "warp_crs": Utils.crs_warp,
    "remove_empty": Utils.remove_empty,
    "netcdf_to_geotiff": Utils.extract_polarization_band,
    "copy_dir": Utils.copy_dir,
    "trimmer_256": Utils.trimmer_256,
    # "clipper": Clipper.start_clipper
}  # TODO later add clipper, denoiser, snap executor and unit converter

pre_init_dict = {
    "align_raster": Utils.get_reference_geotransform,
    "sort_output": Utils.create_sorted_outputs,
}
