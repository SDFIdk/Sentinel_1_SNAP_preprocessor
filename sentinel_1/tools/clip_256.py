from osgeo import gdal, ogr
import shutil
import sys
import tempfile
import os
from pathlib import Path
from sentinel_1.tools.tool import Tool
from sentinel_1.utils import Utils
import rasterio as rio
from rasterio.windows import Window


class Clip256(Tool):
    def __init__(self, input_data, shape, crs, threads = 1):
        self.input_dir = input_data
        self.shape = shape
        self.crs = crs
        self.threads = threads


    def loop(self, input_file):
        """
        Clips a geotiff to a rasters extent, padded to output a resolution divisible by 256
        Takes shape, crs and input_dir
        """
        self.shape = Utils.shape_to_crs(
            shape=self.shape, crs_geotiff=input_file, output_shape=self.input_dir
        )
        ds = ogr.Open(self.shape)
        layer = ds.GetLayer()
        extent = layer.GetExtent()
        minX, maxX, minY, maxY = extent

        maxX = maxX + 2560
        maxY = maxY + 2560
        nodata_value = -9999

        src = gdal.Open(input_file, gdal.GA_ReadOnly)
        src_srs = src.GetProjection()

        warp_options = gdal.WarpOptions(
            outputBounds=[minX, minY, maxX, maxY],
            cutlineDSName=self.shape,
            cropToCutline=True,
            dstNodata=nodata_value,
            srcSRS=src_srs,
            dstSRS=self.crs,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
            tmp_file_path = tmp_file.name

        _ = gdal.Warp(tmp_file_path, src, options=warp_options)

        ds = None
        src = None

        with rio.open(tmp_file_path) as src:
            new_width = (src.width // 256) * 256
            new_height = (src.height // 256) * 256

            window = Window(0, 0, new_width, new_height)
            clipped_data = src.read(window=window)
            new_transform = src.window_transform(window)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
                tmp_file_path_2 = tmp_file.name

            with rio.open(
                tmp_file_path_2,
                "w",
                driver="GTiff",
                height=new_height,
                width=new_width,
                count=src.count,
                dtype=str(clipped_data.dtype),
                crs=self.crs,
                nodata=-9999,
                transform=new_transform,
            ) as dst:
                dst.write(clipped_data)

        shutil.move(tmp_file_path_2, input_file)
