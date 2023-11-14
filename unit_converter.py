import rasterio as rio
import numpy as np
from glob import glob

def db_to_linear(db_geotiff, zero_max = False):
    with rio.open(db_geotiff, 'r+') as src:
        sar_db = src.read(1)
        
        if zero_max: zero_max_func(sar_db)
        sar_linear = 10.0 ** (sar_db / 10.0)
        src.write(sar_linear, 1)
    return 

def power_transfom_to_linear(lin_geotiff, zero_max = False):
    with rio.open(lin_geotiff, 'r+') as src:
        sar_power = src.read(1)
        if zero_max: zero_max_func(sar_power)

        sar_linear = sar_power**10
        src.write(sar_linear, 1)
    return

def linear_to_db(lin_geotiff, zero_max = False):
    with rio.open(lin_geotiff, 'r+') as src:
        sar_linear = src.read(1)

        sar_db = 10.0 * np.log10(sar_linear)
        if zero_max: zero_max_func(sar_db)
        src.write(sar_db, 1)
    return 

def linear_to_power_transform(lin_geotiff, zero_max = False):
    with rio.open(lin_geotiff, 'r+') as src:
        sar_linear = src.read(1)

        sar_power = sar_linear**0.1
        if zero_max: zero_max_func(sar_power)
        src.write(sar_power, 1)
    return

def only_zero_max_conversion(geotiff):
    with rio.open(geotiff, 'r+') as src:
        dataset = src.read(1)
        zero_max_func(dataset)
        src.write(dataset, 1)
    return

def zero_max_func(dataset):
    dataset[dataset > 0] = 0
    return

def no_op(geotiff, zero_max = False): return

def convert_unit(geotiff_dir, source_unit, destination_unit, zero_max = False):
    input_file_list = glob(geotiff_dir + '*.tif')
    assert len(input_file_list) != 0, (
        f'No geotiffs in {geotiff_dir}'
    )

    if source_unit == destination_unit and zero_max:
        print('## Setting max values to 0')
        for i, geotiff in enumerate(input_file_list):
            print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')
            only_zero_max_conversion(geotiff)
        return

    print(f'## Converting from {source_unit} to {destination_unit}...')
    for i, geotiff in enumerate(input_file_list):
        print('# ' + str(i+1) + ' / ' + str(len(input_file_list)), end = '\r')

        source_unit_functions[source_unit](geotiff, zero_max)
        destination_unit_functions[destination_unit](geotiff)
    return


source_unit_functions = {
    'decibel': db_to_linear,
    'power': power_transfom_to_linear,
    'linear': no_op
    }
destination_unit_functions = {
    'decibel': linear_to_db,
    'power': linear_to_power_transform,
    'linear': no_op
}