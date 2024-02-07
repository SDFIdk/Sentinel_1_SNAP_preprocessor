import rasterio as rio
import numpy as np
from glob import glob

"""
Converts units from raw backscatter to decibel or "power transform". 
"""


def convert_unit(geotiff_dir, source_unit, destination_unit, zero_max=False):
    np.seterr(divide = 'ignore')
    if isinstance(geotiff_dir, list):
        input_file_list = geotiff_dir
    else:
        input_file_list = glob(geotiff_dir + "*.tif")

    assert len(input_file_list) != 0, f"No geotiffs in {geotiff_dir}"

    if source_unit == destination_unit and zero_max:
        assert source_unit != "linear", "## Cannot set linear values to zero!"
        print("## Setting max values to 0")
        for i, geotiff in enumerate(input_file_list):
            print("# " + str(i + 1) + " / " + str(len(input_file_list)), end="\r")
            only_zero_max_conversion(geotiff)
        return

    zero_max_out = False
    if zero_max and source_unit == "linear":
        zero_max_out = True
    zero_max_in = False
    if zero_max and destination_unit == "linear":
        zero_max_in = True

    print(f"## Converting from {source_unit} to {destination_unit}...")
    for i, geotiff in enumerate(input_file_list):
        print("# " + str(i + 1) + " / " + str(len(input_file_list)), end="\r")

        with rio.open(geotiff, "r+") as src:
            dataset = src.read(1)
            dataset = generic_transform(
                dataset, source_to_linear[source_unit], zero_max_in
            )
            dataset = generic_transform(
                dataset, linear_to_dest[destination_unit], zero_max_out
            )
            src.write(dataset, 1)
    return


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
