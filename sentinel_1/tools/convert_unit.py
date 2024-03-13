import sys
import rasterio as rio
import numpy as np

from sentinel_1.tools.tool import Tool


class ConvertUnit(Tool):
    def __init__(self, input_dir, source_unit, destination_unit, zero_max=False, threads = 1):
        self.input_dir = input_dir
        self.source_unit = source_unit
        self.destination_unit = destination_unit
        self.zero_max = zero_max
        self.threads = threads


    def printer(self):
        print(f"## Converting from {self.source_unit} to {self.destination_unit}...")

    def loop(self, input_file):
        """
        Converts units from raw backscatter to decibel or "power transform".
        True zero_max will cap values of non linear at zero.
        Takes source_unit, desitnation_unit and zero_max
        """

        def only_zero_max_conversion(geotiff):
            with rio.open(geotiff, "r+") as src:
                dataset = src.read(1)
                zero_max_func(dataset)
                src.write(dataset, 1)
            return

        def zero_max_func(dataset):
            dataset[dataset > 0] = 0
            return dataset

        def no_op(geotiff, zero_max=False):
            return geotiff

        def generic_transform(dataset_in, equation, zero_max=False):
            dataset_out = equation(dataset_in)
            if zero_max:
                dataset_out = zero_max_func(dataset_out)
            return dataset_out

        source_to_linear = {
            "decibel": lambda a: 10.0 ** (a / 10.0),
            "power": lambda a: a**10,
            "linear": no_op,
        }
        linear_to_dest = {
            "decibel": lambda a: 10.0 * np.log10(a),
            "power": lambda a: a**0.1,
            "linear": no_op,
        }

        np.seterr(divide="ignore")

        if self.source_unit == self.destination_unit and self.zero_max:
            assert self.source_unit != "linear", "## Cannot set linear values to zero!"
            only_zero_max_conversion(input_file)
            return

        zero_max_out = False
        if self.zero_max and self.source_unit == "linear":
            zero_max_out = True
        zero_max_in = False
        if self.zero_max and self.destination_unit == "linear":
            zero_max_in = True

        with rio.open(input_file, "r+") as src:
            dataset = src.read(1)
            dataset = generic_transform(
                dataset, source_to_linear[self.source_unit], zero_max_in
            )
            dataset = generic_transform(
                dataset, linear_to_dest[self.destination_unit], zero_max_out
            )
            src.write(dataset, 1)
