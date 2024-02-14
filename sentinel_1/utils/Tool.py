class Tool:
    # def __init__(self, input_dir, extension, threads = 1, polarization = None):
    #     self.input_dir = input_dir
    #     self.extension = extension
    #     self.threads = threads
    #     self.polarization = polarization

    #     self.tool_dict = {
    #         "align_raster": AlignRaster(),
    #         # "split_geotiff": Utils.split_polarizations,
    #         # "change_resolution": Utils.change_raster_resolution,
    #         # "sort_output": Utils.sort_output,
    #         # "warp_crs": Utils.crs_warp,
    #         # "remove_empty": Utils.remove_empty,
    #         # "copy_dir": Utils.copy_dir,
    #         # "trimmer_256": Utils.trimmer_256,
    #         # "convert_unit": Utils.convert_unit,
    #         # "netcdf_to_geotiff": Utils.extract_polarization_band_incidence,
    #         # "TEST_FUNK": Utils.TEST_FUNK,
    #         # "clipper": Clipper.start_clipper
    #     }   #TODO later add clipper, denoiser and snap executor

    #     self.pre_init_dict = {
    #         "align_raster": Utils.get_reference_geotransform,
    #         "sort_output": Utils.create_sorted_outputs,
    #     }

    def run(self, input_file, **kwargs):
        raise NotImplementedError("## Tool not recognized!")
