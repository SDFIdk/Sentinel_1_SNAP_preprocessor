import rasterio
import numpy as np
from PIL import Image
import sys

def calculate_average_band(file_path):
    """
    Calculate and print the average value of the first band in a GeoTIFF file.

    Parameters:
    - file_path (str): The path to the input GeoTIFF file.
    """
    with rasterio.open(file_path) as src:
        band1 = src.read(1)  # Read the first band
        average_value = band1.mean()
        print(f"Average value of the first band: {average_value}")

        return band1, src.profile

def convert_to_jpeg(band_data, profile, output_path):
    """
    Convert the first band of a GeoTIFF file to a JPEG file.

    Parameters:
    - band_data (numpy.ndarray): The data of the first band.
    - profile (dict): The profile (metadata) of the GeoTIFF file.
    - output_path (str): The path to the output JPEG file.
    """
    # Normalize the band data to the range [0, 255]
    band_min = band_data.min()
    band_max = band_data.max()
    normalized_band = (255 * (band_data - band_min) / (band_max - band_min)).astype(np.uint8)

    # Create an image from the normalized data
    img = Image.fromarray(normalized_band, mode='L')
    img.save(output_path, format='JPEG')
    print(f"Converted band 1 to JPEG and saved as {output_path}")


# input_file = 'J:/javej/geus_total_rerun/whole_dk_mosaic/sentinel_1/bu/S1A_IW_GRDH_1SDV_20240111T171839_20240111T171904_052062_064AC0_84B3'
input_file = 'J:/javej/geus_total_rerun/whole_dk_mosaic/sentinel_1/bu_split/S1A_IW_GRDH_1SDV_20240110T052413_20240110T052438_052040_064A04_6F13_ORBIT_MOSAIC_VV_DSC.tif'
output_file = 'test_scripts/output.jpg'

band_data, profile = calculate_average_band(input_file)

sys.exit()

if output_file:
    convert_to_jpeg(band_data, profile, output_file)
