import os
import shutil
import sys
from sentinel_1.tools.tool import Tool
from sentinel_1.utils import Utils


class SortOutput(Tool):
    def __init__(
        self, input_dir, result_dir, denoise_mode, unit, resolution, polarization
    ):
        self.input_dir = input_dir
        self.result_dir = result_dir
        self.denoise_mode = denoise_mode
        self.unit = unit
        self.resolution = resolution
        self.polarization = polarization

    def loop(self, input_file):
        """
        Sorts geotiffs into folder based on polarizaton and orbital direction
        Requires "create_sorted_outputs" function to be run beforehand
        Takes output_sub_dir and polarization
        """
        polarization = self.polarization
        if not isinstance(polarization, list):
            polarization = [polarization]
        file_polarization = None
        for pol in polarization:
            if pol in input_file:
                file_polarization = pol

        product_dir = self.denoise_mode + "_" + str(self.resolution) + "m_" + self.unit

        sort_dir = os.path.join(self.result_dir, product_dir, file_polarization)
        Utils.check_create_folder(sort_dir)
        sort_filename = os.path.join(sort_dir, os.path.basename(input_file))
        shutil.copyfile(input_file, sort_filename)
        return
