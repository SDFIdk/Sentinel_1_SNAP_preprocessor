from osgeo import (
    gdal,
)  # BUG #CURSED has to be on top, otherwise "No module named _gdal" ???
import os
from pathlib import Path
import numpy as np
import xarray as xr
from xrspatial.focal import mean as xrs_mean

from sentinel_1.tools.tif_tool import TifTool
from sentinel_1.utils import Utils


class Denoiser(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

    def printer():
        print(f"## Applying mean filter...")

    def process_file(self, input_file):

        xds = xr.open_dataset(input_file, engine="rasterio").to_array().squeeze()
        
        xds_bands = range(xds.shape[0])
        processed_bands = []
        for i in xds_bands - 1:
            processed_band = xrs_mean(xds[i, :, :])
            processed_bands.append(processed_band)
        
        processed_bands.append(xds[-1, :, :])
        
        nds = xr.concat(processed_bands, dim='band').to_numpy()

        original_dataset = gdal.Open(input_file, gdal.GA_Update)
        for i in xds_bands:
            original_dataset.GetRasterBand(i).WriteArray(nds[i, :, :])