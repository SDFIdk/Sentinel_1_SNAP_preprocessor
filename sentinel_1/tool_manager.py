import sys
import os
from multiprocessing.pool import Pool
from sentinel_1.utils import Utils


class ToolManager:
    def __init__(self, input_dir, extension, threads=1, polarization=None):
        self.input_dir = input_dir
        self.extension = extension
        self.threads = threads
        self.polarization = polarization

        self.tool_dict = {
            # "split_geotiff": Utils.split_polarizations,
            "change_resolution": Utils.change_raster_resolution,
            "sort_output": Utils.sort_output,
            "align_raster": Utils.align_raster,
            "warp_crs": Utils.crs_warp,
            "remove_empty": Utils.remove_empty,
            "copy_dir": Utils.copy_dir,
            "clip_256": Utils.clip_256,
            "trimmer_256": Utils.trimmer_256,
            "convert_unit": Utils.convert_unit,
            "netcdf_to_geotiff": Utils.extract_polarization_band_incidence,
            # "TEST_FUNK": Utils.TEST_FUNK,
        }  # TODO later add denoiser and snap executor

        self.pre_init_dict = {
            "align_raster": Utils.get_reference_geotransform,
            "sort_output": Utils.create_sorted_outputs,
        }

    def util_starter(self, tool, **kwargs):
        kwargs.update(vars(self).copy())  # passes self.to kwargs.

        if self.pre_init_dict.get(tool):
            kwargs = self.pre_init_dict.get(tool)(**kwargs)

        if self.threads == 1:
            self.start_singleproc(tool, **kwargs)
        elif self.threads > 1:
            print("fix multiproc. first!")
            self.start_singleproc(tool, **kwargs)
            # self.start_multiproc(tool, self.threads, kwargs)
        else:
            raise Exception(
                f"## Thread var must contain number greater than 0. Got {self.threads}"
            )

        # a "tool printer" would display a single print the statement the tools previously provided

    def start_singleproc(self, tool, **kwargs):
        if isinstance(self.input_dir, list):
            input_file_list = self.input_dir
        else:
            input_file_list = Utils.file_list_from_dir(self.input_dir, self.extension)

        for i, input_file in enumerate(input_file_list):
            print("# " + str(i + 1) + " / " + str(len(input_file_list)), end="\r")

            self.tool_dict[tool](input_file, **kwargs)

        print("Done!")

    def start_multiproc(self, tool, threads, **kwargs):
        # items = []
        # for input_file in Utils.file_list_from_dir(self.input_dir, self.extension):
        #     items.append((input_file, **kwargs))

        # for result in Pool.starmap(self.tool_dict[tool], items):
        #     print() #?
        #     #also use that multiproc. thing that lets you specify threads.

        # with Pool(threads) as p:
        #     p.map(self.tool_dict[tool], (items))

        import concurrent.futures

        input_files = Utils.file_list_from_dir(self.input_dir, self.extension)

        def process_file(tool, input_file, **kwargs):
            return self.tool_dict[tool](input_file, **kwargs)

        with concurrent.futures.ProcessPoolExecutor(max_workers=threads) as executor:
            tasks = [
                executor.submit(process_file, tool, file, **kwargs)
                for file in input_files
            ]
            results = [task.result() for task in concurrent.futures.as_completed(tasks)]
