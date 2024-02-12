import zipfile
from osgeo import gdal
import xml.etree.ElementTree as ET
import os
import sys
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio.mask import mask
from rasterio.windows import Window
from pathlib import Path
from glob import glob
import shutil
import uuid
import pyproj

class Utils(object):

    def gdal_error_handler(err_class, err_num, err_msg):
        errtype = {
                gdal.CE_None:'None',
                gdal.CE_Debug:'Debug',
                gdal.CE_Warning:'Warning',
                gdal.CE_Failure:'Failure',
                gdal.CE_Fatal:'Fatal'
        }
        err_msg = err_msg.replace('\n',' ')
        err_class = errtype.get(err_class, 'None')
        print('Error Number: %s' % (err_num))
        print('Error Type: %s' % (err_class))
        print('Error Message: %s' % (err_msg))


    def file_list_from_dir(directory, extension):
        file_list = glob(directory + extension)
        assert len(file_list) != 0, f'## No {extension} files in {directory}!'
        return file_list
    
    
    def is_valid_epsg(epsg_code):
        try:
            pyproj.CRS.from_epsg(epsg_code)
            return True
        except pyproj.exceptions.CRSError:
            return False
        

    def check_create_folder(directory):
        Path(directory).mkdir(exist_ok = True)


    def aoi_cloud_cover(inputProductPath, shape):

        scl_filename = Utils.extract_scl(inputProductPath)
        if scl_filename == None: return

        if not shape == None:
            options = gdal.WarpOptions(cutlineDSName = shape, cropToCutline = True, dstSRS = 'EPSG:4326')
            Utils.open_option_warp_move(scl_filename, options, 'tmp/clip_scl.jp2')

        cloud_percentage = Utils.get_cloud_percentage(scl_filename)
        del(scl_filename)
        return cloud_percentage
    

    def get_cloud_percentage(scl_filename):

        scl_ds = rio.open(scl_filename).read(1)

        cloud_pixels = np.sum(np.isin(scl_ds, [8, 9]))    #8, 9 represents medium and high probability cloud classes in SRC
        total_data_pixels = scl_ds.size - np.sum(np.isin(scl_ds, [0]))

        scl_ds = None
        return (cloud_pixels / total_data_pixels) * 100

    
    def extract_scl(inputProductPath):
        with zipfile.ZipFile(inputProductPath, 'r') as zip_ref:
            scl_file = [f for f in zip_ref.namelist() if '_SCL_20m.jp2' in f]

            if scl_file == None: 
                print(f"# {inputProductPath} has no SCL band!")
                return None

            scl_filename = 'tmp/' + os.path.basename(scl_file[0])

            with zip_ref.open(scl_file[0]) as source, open(scl_filename, 'wb') as target:
                target.write(source.read())
            return(scl_filename)


    def shape_to_geojson(output, shape):
        shp_file = gpd.read_file(shape)
        geojson = output + 'tmp.geojson'
        shp_file.to_file(geojson, driver='GeoJSON')
        return geojson
    

    def unzip_data_to_dir(data, tmp):
        unzipped_safe = tmp + str(uuid.uuid4())
        Path(unzipped_safe).mkdir(exist_ok = True)
        with zipfile.ZipFile(data, 'r') as zip_ref:
            zip_ref.extractall(unzipped_safe)
        
        return unzipped_safe
    

    def remove_folder(folder):
        shutil.rmtree(folder)
    
    
    def crs_warp(dataset, crs, output):
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        src_SRS = gdal_dataset.GetProjection()
        # print(src_SRS)
        # print(x_res)
        # print(y_res)
        # print(crs)

        # options = gdal.WarpOptions(format = "GTiff", srcSRS = src_SRS, dstSRS = crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)     
        options = gdal.WarpOptions(format = "GTiff", srcSRS = src_SRS, dstSRS = crs, resampleAlg=gdal.GRA_NearestNeighbour)     

        gdal.Warp(output, gdal_dataset, options = options)
        shutil.move(output, dataset)
    
    
    def open_option_warp_move(dataset, options, output):
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)
        gdal.Warp(output, gdal_dataset, options = options)
        shutil.move(output, dataset)


    def remove_empty_files(geotiff, max_empty_percent):
        with rio.open(geotiff, 'r') as src:
            data = src.read(1)

        zero_pixel_count = (data == 0).sum()
        total_pixels = data.size
        percentage = (zero_pixel_count / total_pixels) * 100

        data = None

        if percentage >= max_empty_percent:
            print(f'# Removed {geotiff}, data coverage: {str(100 - percentage)} %')
            os.remove(geotiff)

