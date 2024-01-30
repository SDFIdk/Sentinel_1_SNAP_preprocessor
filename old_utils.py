import zipfile
from osgeo import gdal, osr
import os
import sys
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio.crs import CRS
from pathlib import Path
import glob
import shutil
import uuid
import pyproj

class OLD_Utils(object):

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
        

    def file_list_from_dir(directory, extension, accept_no_files = False):
        """
        Returns file content of dir with given extension
        """
        file_list = glob.glob(directory + extension)
        if not accept_no_files: 
            assert len(file_list) != 0, (
                f'## No {extension} files in {directory}!'
                )
        return file_list
    
    
    def is_valid_epsg(epsg_code):
        """
        Checks whether provided EPSG code is valid
        """
        try:
            pyproj.CRS.from_epsg(epsg_code)
            return True
        except pyproj.exceptions.CRSError:
            return False
        

    def check_create_folder(directory):
        Path(directory).mkdir(exist_ok = True)
    

    def shape_to_geojson(output, shape):
        shp_file = gpd.read_file(shape)
        geojson = output + 'tmp.geojson'
        shp_file.to_file(geojson, driver='GeoJSON')
        return geojson


    def extract_polarization_band(input_file, geotiff_output_dir, polarization):
        """
        Splits a netcdf into constituent bands depending depending on polarization
        """

        extension = Path(input_file).suffix
        input_dataset = gdal.Open(input_file, gdal.GA_ReadOnly)

        for subdataset in input_dataset.GetSubDatasets():

            subdataset_name, _ = subdataset
            band = gdal.Open(subdataset_name)
            metadata = band.GetMetadata()

            orbit = metadata['/Metadata_Group/Abstracted_Metadata/NC_GLOBAL#PASS']

            if orbit == 'ASCENDING': orbit_direction = 'ASC'
            elif orbit == 'DESCENDING': orbit_direction = 'DSC'
            else: 
                raise Exception('# Orbital direction not found in NetCDF metadata')

            for pol in polarization:
                if '_' + pol in subdataset_name:
                    band_type = pol
                    break
            assert band_type, (
                '# Polarization not found in NetCDF metadata'
            )

            for key, value in metadata.items():
                if 'srsName' in key: 
                    _, _, crs = value.partition('#')
                    crs = f'EPSG:{crs}'
                    break
            assert crs, (
                '# CRS not found in NetCDF metadata'
            )
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(int(crs.split(':')[1]))

            translate_options = gdal.TranslateOptions(
                format = "GTiff",
                options = ["TILED=YES", "COMPRESS=LZW"],
                outputType = gdal.GDT_Float32,
                outputSRS=srs.ExportToWkt()
            )

            band_info = band_type + '_' + orbit_direction
            
            filename = os.path.basename(input_file).replace(extension, '_') + band_info + "_band.tif"
            output_geotiff = os.path.join(geotiff_output_dir, filename)
            
            gdal.Translate(output_geotiff, band, options=translate_options)

        input_dataset = None        
        return


    # def crs_assign(self, input_raster, output_raster, crs):
    #     """
    #     Assigns a CRS but does not warp. Only useful for datasets which are referenced but have no metadata
    #     """
    #     with rio.open(input_raster) as src:
    #         data = src.read()
    #         meta = src.meta.copy()

    #     meta.update({'crs': CRS.from_string(crs)})

    #     with rio.open(output_raster, 'w', **meta) as dst:
    #         dst.write(data)

    #     shutil.move(output_raster, input_raster)


    def unzip_data_to_dir(data, tmp):
        """
        Outputs content of zipfile to randomly named folder.
        Used for SAFE files
        """
        unzipped_safe = tmp + str(uuid.uuid4())
        Path(unzipped_safe).mkdir(exist_ok = True)
        with zipfile.ZipFile(data, 'r') as zip_ref:
            zip_ref.extractall(unzipped_safe)
        
        return unzipped_safe
    

    def remove_folder(folder):
        shutil.rmtree(folder)
    
    
    def crs_warp(dataset, crs, output):
        """
        Warps a raster to a new crs
        """
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        options = gdal.WarpOptions(format = "GTiff", dstSRS = crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)     
        gdal.Warp(output, gdal_dataset, options = options)
        shutil.move(output, dataset)


    def change_raster_resolution(input_raster_path, output_raster_path, x_size, y_size):
        """
        Resamples a raster to a new resolution
        """
        input_raster = gdal.Open(input_raster_path)

        warp_options = gdal.WarpOptions(xRes=x_size, yRes=y_size, resampleAlg='near', format='GTiff')
        output_raster = gdal.Warp(output_raster_path, input_raster, options=warp_options)

        input_raster = None
        output_raster = None
        shutil.move(output_raster_path, input_raster_path)


    def split_polarizations(geotiff_dir, input_geotiff, polarization):
        print('## Splitting geotiffs into single bands...')

        with rio.open(input_geotiff) as src:
            meta = src.meta.copy()

            for band in range(1, src.count + 1):
                data = src.read(band)

                output_filename = f"{geotiff_dir}/band________{band}.tif"
                print(output_filename)

                meta = src.meta.copy()
                meta.update({'count': 1})

                with rio.open(output_filename, 'w', **meta) as dst:
                    dst.write(data, 1)

    
    def create_sorted_outputs(output, polarization, folder_name):
        """
        Function creates ASC and DSC folders for each polarization given.
        """
        Path(folder_name).mkdir(exist_ok = True)
        output = output + folder_name
        Path(output).mkdir(exist_ok = True)

        for pol in polarization:
            Path(output + pol + '_ASC/').mkdir(exist_ok = True)
            Path(output + pol + '_DSC/').mkdir(exist_ok = True)
        return output
    
    
    def find_empty_raster(geotiff):
        """
        Finds geotiffs with no data
        """
        with rio.open(geotiff) as src:
            for i in range(1, src.count + 1):
                data = src.read(i)

                if not np.all(np.isnan(data)):
                    return False
        return True

        
    def sort_outputs(tif, polarization, output):

        if not isinstance(polarization, list):
            polarization = [polarization]

        file_polarization = None
        for pol in polarization:
            if pol in tif:  file_polarization = pol
        if file_polarization == None: print('# ERROR: No polarization information in file!')

        orbit_dir = None
        if '_ASC_' in tif: orbit_dir = 'ASC'
        elif '_DSC_' in tif: orbit_dir = 'DSC'
        if orbit_dir == None: print('# ERROR: No orbital direction information in file!')

        if None in (file_polarization, orbit_dir):
            Path(output + 'unsorted/').mkdir(exist_ok = True)
            shutil.copyfile(tif, output + 'unsorted/')
            return

        sort_dir = output + file_polarization + '_' + orbit_dir + '/'
        sort_filename = sort_dir + os.path.basename(tif)
        shutil.copyfile(tif, sort_filename)
        return
    
    
    def get_reference_geotransform(input_file_list):
        #pre init function!
        #largest file will in all likelihood contain an image which overlaps whole shape
        reference_file = max(input_file_list, key=os.path.getsize)

        reference = gdal.Open(reference_file)
        reference_geotransform = reference.GetGeoTransform()
        reference = None

        arg_name = "reference_geotransform"

        return reference_geotransform, arg_name
    

    def align_raster(raster_path, output_path, reference_geotransform):
        gdal.Warp(output_path,
                raster_path,
                xRes=reference_geotransform[1],
                yRes=-reference_geotransform[5],
                targetAlignedPixels=True,
                resampleAlg=gdal.GRA_NearestNeighbour
                )
        shutil.move(output_path, raster_path)
                    

gdal.UseExceptions()
