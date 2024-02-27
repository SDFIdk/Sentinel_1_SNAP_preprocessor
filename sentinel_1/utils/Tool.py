from sentinel_1.utils.align_raster_superclass_example import AlignRaster
from sentinel_1.utils import Utils

from concurrent.futures import ProcessPoolExecutor, wait

class Tool:
    threads = 1

    def __init__(self, extension, input_dir=None):
        self.input_dir = input_dir
        self.ext = extension

    def setup(self):
        #this part should call the setup function somehow
        pass

    def loop(self, input_file):
        pass

    def teardown(self):
        pass

    def files(self):
        Utils.file_list_from_dir(self.input_dir, self.ext)

    def run(self):
        self.setup()

        if self.threads > 1:
            self._run_parallel()
        else:
            self._run_linear()

        self.teardown()

    def _run_parallel(self):
        files = self.files()

        with ProcessPoolExecutor(self.threads) as exc:
            futures = [exc.submit(self.loop, input_file) for input_file in files]
            wait(futures)

    def _run_linear(self):
        files = self.files()
        for input_file in files:
            self.loop(input_file)

















    # def __init__(self, input_dir, extension, threads = 1, polarization = None):
    #     self.input_dir = input_dir
    #     self.extension = extension
    #     self.threads = threads
    #     self.polarization = polarization

    #     self.tool_dict = {
    #         "align_raster": AlignRaster(),
    # #         # "split_geotiff": Utils.split_polarizations,
    # #         # "change_resolution": Utils.change_raster_resolution,
    # #         # "sort_output": Utils.sort_output,
    # #         # "warp_crs": Utils.crs_warp,
    # #         # "remove_empty": Utils.remove_empty,
    # #         # "copy_dir": Utils.copy_dir,
    # #         # "trimmer_256": Utils.trimmer_256,
    # #         # "convert_unit": Utils.convert_unit,
    # #         # "netcdf_to_geotiff": Utils.extract_polarization_band_incidence,
    # #         # "TEST_FUNK": Utils.TEST_FUNK,
    # #         # "clipper": Clipper.start_clipper
    #     }   #TODO later add clipper, denoiser and snap executor

    # #     self.pre_init_dict = {
    # #         "align_raster": Utils.get_reference_geotransform,
    # #         "sort_output": Utils.create_sorted_outputs,
    # #     }

    # def run(self, input_file, **kwargs):
    #     raise NotImplementedError("## Tool not recognized!")
