import rasterio as rio
from rasterio.features import geometry_mask
import os
import shutil
import sys
import geopandas as gpd

from sentinel_1.tools.tool import Tool


class LandSeaMask(Tool):
    def __init__(self, input_dir, land_sea_mask, threads = 1):
        self.input_dir = input_dir
        self.land_sea_mask = land_sea_mask
        self.threads = threads


    def printer(self):
        print(f"## Applying land/sea mask...")

    def loop(self, input_file):
        """
        Sets all values in a raster outside a polygon to noData
        Default set to the Danish Landpolygon
        Takes land_sea_mask, input_dir
        """

        shape = gpd.read_file(self.land_sea_mask)

        with rio.open(input_file) as src:
            mask = geometry_mask(
                [geometry for geometry in shape.geometry],
                transform=src.transform,
                invert=True,
                out_shape=(src.height, src.width),
            )

            raster_data = src.read(
                1
            )  # only necessary to read the data band which is always first

            raster_data[~mask] = -9999

            new_meta = src.meta.copy()
            new_meta["nodata"] = -9999

            tmp_geotiff = os.path.join(self.input_dir, "tmp.tif")
            with rio.open(tmp_geotiff, "w", **new_meta) as dst:
                dst.write(raster_data, 1)
        shutil.move(tmp_geotiff, input_file)
