import sys
import os
from sentinel_1.utils import Utils
from concurrent.futures import ThreadPoolExecutor

class ToolManager:
    def __init__(self, input_dir, extension, threads=1, polarization=None):
        self.input_dir = input_dir
        self.extension = extension
        self.threads = threads
        self.polarization = polarization

        self.tool_dict = {
            "split_polarizations": Utils.split_polarizations,
            # "change_resolution": Utils.change_raster_resolution,
            # "sort_output": Utils.sort_output,
            # "align_raster": Utils.align_raster,
            # "warp_crs": Utils.crs_warp,
            # "remove_empty": Utils.remove_empty,
            # "copy_dir": Utils.copy_dir,
            # "clip_256": Utils.clip_256,
            # "trimmer_256": Utils.trimmer_256,
            # "convert_unit": Utils.convert_unit,
            # "land_sea_mask": Utils.land_sea_mask,
            # "TEST_FUNK": Utils.TEST_FUNK,
        }  # TODO later add denoiser and snap executor

        self.pre_init_dict = {
            "align_raster": Utils.get_reference_geotransform,
        }

    def util_starter(self, tool, **kwargs):
        kwargs.update(vars(self).copy())  # passes self to kwargs.

        if self.pre_init_dict.get(tool):
            kwargs = self.pre_init_dict.get(tool)(**kwargs)

        if self.threads == 1:
            self.start_singleproc(tool, **kwargs)
        elif self.threads > 1:
            self.start_multiproc(tool, **kwargs)
        else:
            raise Exception(
                f"## Thread var must contain number greater than 0. Got {self.threads}"
            )

    def start_singleproc(self, tool, **kwargs):
        if isinstance(self.input_dir, list):
            input_file_list = self.input_dir
        else:
            input_file_list = Utils.file_list_from_dir(self.input_dir, self.extension)

        for i, input_file in enumerate(input_file_list):
            print("# " + str(i + 1) + " / " + str(len(input_file_list)), end="\r")

            print(self.tool_dict)
            print(tool)
            self.tool_dict[tool](input_file, **kwargs)

    def start_multiproc(self, tool, **kwargs):
        if isinstance(self.input_dir, list):
            input_file_list = self.input_dir
        else:
            input_file_list = Utils.file_list_from_dir(self.input_dir, self.extension)
        
        def worker(input_file):
            self.tool_dict[tool](input_file, **kwargs)
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(worker, input_file) for input_file in input_file_list]
            
            for future in futures:
                try:
                    future.result() 
                except Exception as exc:
                    print(f"## Generated an exception: {exc}")