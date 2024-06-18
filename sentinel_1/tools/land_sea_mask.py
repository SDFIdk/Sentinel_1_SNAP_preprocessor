import rasterio as rio
from rasterio.features import geometry_mask
import os
import shutil
import sys
import geopandas as gpd
import uuid

from sentinel_1.tools.tif_tool import TifTool


class LandSeaMask(TifTool):
    def __init__(self, input_dir, land_sea_mask, threads = 1):
        self.input_dir = input_dir
        self.land_sea_mask = land_sea_mask
        self.threads = threads


    def printer(self):
        print(f"## Applying land/sea mask...")

    # def process_file(self, input_file):
    #     """
    #     Sets all values in a raster outside a polygon to noData
    #     Default set to the Danish Landpolygon
    #     Takes land_sea_mask, input_dir
    #     """

    #     shape = gpd.read_file(self.land_sea_mask)

    #     with rio.open(input_file) as src:
    #         mask = geometry_mask(
    #             [geometry for geometry in shape.geometry],
    #             transform=src.transform,
    #             invert=True,
    #             out_shape=(src.height, src.width),
    #         )

    #         raster_data = src.read(1)
    #         incidence_data = src.read(2)

    #         raster_data[~mask] = -9999

    #         new_meta = src.meta.copy()
    #         new_meta["nodata"] = -9999

    #         tmp_name = uuid.uuid4()[0:7] + "tmp.tif"
    #         tmp_geotiff = os.path.join(self.input_dir, tmp_name)
    #         with rio.open(tmp_geotiff, "w", **new_meta) as dst:
    #             dst.write(raster_data, 1)
    #             dst.write(incidence_data, 2)
    #     shutil.move(tmp_geotiff, input_file)

    #     return input_file

    def process_file(self, input_file):
        """
        Sets all values in a raster outside a polygon to noData
        Default set to the Danish Landpolygon
        Takes land_sea_mask, input_dir
        """

        shape = gpd.read_file(self.land_sea_mask)

        with rio.open(input_file) as src:
            band_names = [src.descriptions[i] for i in range(src.count)]

            mask = geometry_mask(
                [geometry for geometry in shape.geometry],
                transform=src.transform,
                invert=True,
                out_shape=(src.height, src.width),
            )

            raster_data = src.read(1)
            incidence_data = src.read(2)

            raster_data[~mask] = -9999

            new_meta = src.meta.copy()
            new_meta["nodata"] = -9999

            tmp_name = str(uuid.uuid4())[:7] + "_tmp.tif"
            tmp_geotiff = os.path.join(self.input_dir, tmp_name)
            
            with rio.open(tmp_geotiff, "w", **new_meta) as dst:
                dst.write(raster_data, 1)
                dst.write(incidence_data, 2)
                
                dst.set_band_description(1, band_names[0])
                dst.set_band_description(2, band_names[1])
        
        shutil.move(tmp_geotiff, input_file)

        return input_file
