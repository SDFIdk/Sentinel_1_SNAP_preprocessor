from osgeo import gdal, ogr
import os
import sys
import rasterio as rio
import shutil
from rasterio.windows import Window
import geopandas as gpd
from pathlib import Path

from utils import Utils


class Clipper_Util(object):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.geotiff_output_dir = output_dir + "unfinished_geotiffs/"
        self.tmp = output_dir + "tmp/"
        self.denoised_geotiffs = output_dir + "denoised_geotiffs/"

        Utils.check_create_folder(self.tmp)

        gdal.PushErrorHandler(Utils.gdal_error_handler)
        gdal.UseExceptions()

    def shape_to_crs(self, shape, input_dir):
        gdf = gpd.read_file(shape)

        geotiff = Utils.file_list_from_dir(input_dir, "*.tif")[0]
        geotiff_crs = rio.open(geotiff).crs
        gdf_warp = gdf.to_crs(geotiff_crs)

        new_shape_dir = self.output_dir + "crs_corrected_shape/"
        Path(new_shape_dir).mkdir(exist_ok=True)

        output_shape = new_shape_dir + "new_" + os.path.basename(shape)
        gdf_warp.to_file(output_shape)

        return output_shape

    def clip_to_256(self, input_file, kwargs):
        shape = kwargs.get("shape")
        crs = kwargs.get("crs")
        ds = ogr.Open(shape)
        layer = ds.GetLayer()
        extent = layer.GetExtent()
        minX, maxX, minY, maxY = extent

        maxX = maxX + 2560      
        maxY = maxY + 2560
        nodata_value = -9999    #standard nodata value for Sentinel-1

        src = gdal.Open(input_file, gdal.GA_ReadOnly)

        try:
            src_srs = src.GetProjection()
        except:
            src_srs = "EPSG:4326"  # hail mary default CRS

        warp_options = gdal.WarpOptions(
            outputBounds=[minX, minY, maxX, maxY],
            cutlineDSName=shape,
            cropToCutline=True,
            dstNodata=nodata_value,
            srcSRS=src_srs,
            dstSRS=crs,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        _ = gdal.Warp(self.tmp + "clipped_raster.tif", src, options=warp_options)

        ds = None
        src = None

        with rio.open(self.tmp + "clipped_raster.tif") as src:
            new_width = (src.width // 256) * 256
            new_height = (src.height // 256) * 256

            window = Window(0, 0, new_width, new_height)
            clipped_data = src.read(window=window)
            new_transform = src.window_transform(window)

            with rio.open(
                self.tmp + "clipped_raster2.tif",
                "w",
                driver="GTiff",
                height=new_height,
                width=new_width,
                count=src.count,
                dtype=str(clipped_data.dtype),
                crs=crs,
                nodata=-9999,
                transform=new_transform,
            ) as dst:
                dst.write(clipped_data)

        shutil.move(self.tmp + "clipped_raster2.tif", input_file)
