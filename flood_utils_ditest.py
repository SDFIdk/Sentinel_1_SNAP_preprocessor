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

class TEST_Utils(object):

    #functions should in principle output to same folder as input, unless directly specified otherwise.
    #in/out should be either handled by self or by the tool manager.
    

    def __init__(self, netcdf_dir, geotiff_dir):
        if netcdf_dir == None: netcdf_dir = 'netcdf_output/'
        self.netcdf_dir = netcdf_dir
        if geotiff_dir == None: geotiff_dir = 'geotiff_output/'
        self.geotiff_dir = geotiff_dir
        self.tmp = 'tmp/'

        gdal.PushErrorHandler(TEST_Utils.gdal_error_handler)
        gdal.UseExceptions()

    def gdal_error_handler(self, err_class, err_num, err_msg):
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
        

    def file_list_from_dir(self, directory, extension, accept_no_files = False):
        """
        Returns file content of dir with given extension.
        If given a list of extensions, the function will whatever yields any files firt
        under assumption that the folder will only contain one type of files.
        """
        if isinstance(extension, list):
            for ext in extension:
                file_list = glob.glob(directory + extension)
                if file_list: break

            assert file_list, (
                '# No files in input directory!'
            ) 
        else:
            file_list = glob.glob(directory + extension)

        if not accept_no_files: 
            assert len(file_list) != 0, (
                f'## No {extension} files in {directory}!'
                )
        return file_list
    
    
    def is_valid_epsg(self, epsg_code):
        """
        Checks whether provided EPSG code is valid
        """
        try:
            pyproj.CRS.from_epsg(epsg_code)
            return True
        except pyproj.exceptions.CRSError:
            return False
        

    def check_create_folder(self, directory):
        Path(directory).mkdir(exist_ok = True)
    

    def shape_to_geojson(self, **kwargs):
        """
        Converts a shape to geoJSON
        Takes output_file and shape
        """
        shape = kwargs.get('shape')
        output_file = kwargs.get('output_file')

        shp_file = gpd.read_file(shape)
        geojson = output_file + str(uuid.uuid4()) + '.geojson'
        shp_file.to_file(geojson, driver='GeoJSON')
        return geojson


    def extract_polarization_band(self, **kwargs):
        """
        Splits a netcdf into constituent bands depending depending on polarization
        Takes input_file, polarization and output_dir
        """
        input_file = kwargs.get('input_file')
        polarization = kwargs.get('polarization')
        output_dir = kwargs.get('output_dir')

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
            output_geotiff = os.path.join(output_dir, filename)
            
            gdal.Translate(output_geotiff, band, options=translate_options)

        input_dataset = None        
        return


    # def crs_assign(self, input_raster, crs):
    #     """
    #     Assigns a CRS but does not warp. Only useful for datasets which are referenced but have no metadata
    #     """
    #     with rio.open(input_raster) as src:
    #         data = src.read()
    #         meta = src.meta.copy()

    #     meta.update({'crs': CRS.from_string(crs)})

    #     output_raster = str(uuid.uuid4()) + '.tif'
    #     with rio.open(output_raster, 'w', **meta) as dst:
    #         dst.write(data)

    #     shutil.move(output_raster, input_raster)


    def unzip_data_to_dir(self, **kwargs):
        """
        Outputs content of zipfile to randomly named folder.
        Used for SAFE files
        Takes input_file
        """
        input_file = kwargs.get('input_file')

        unzipped_safe = self.tmp + str(uuid.uuid4())
        Path(unzipped_safe).mkdir(exist_ok = True)
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(unzipped_safe)
        
        return unzipped_safe
    

    def remove_folder(self, folder):
        shutil.rmtree(folder)
    
    
    def crs_warp(self, **kwargs):
        """
        Warps a raster to a new crs
        Takes input_file and crs 
        """
        input_file = kwargs.get('input_file')
        crs = kwargs.get('crs')

        gdal_dataset = gdal.Open(input_file)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        output_file = str(uuid.uuid4()) + '.tif'

        options = gdal.WarpOptions(format = "GTiff", dstSRS = crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)     
        gdal.Warp(output_file, gdal_dataset, options = options)
        shutil.move(output_file, input_file)


    def change_raster_resolution(self, **kwargs):
        """
        Resamples a raster to a new resolution
        Takes input_file, x_size, y_size
        """
        input_file = kwargs.get('input_file')
        x_size = kwargs.get('x_size')
        y_size = kwargs.get('y_size')

        input_file = gdal.Open('input_file')

        output_file = str(uuid.uuid4()) + '.tif'

        warp_options = gdal.WarpOptions(xRes=x_size, yRes=y_size, resampleAlg='near', format='GTiff')
        output_raster = gdal.Warp(output_file, input_file, options=warp_options)

        input_file = None
        output_raster = None
        shutil.move(output_file, input_file)


    # def split_polarizations(self, geotiff_dir, input_geotiff, polarization):
    #     print('## Splitting geotiffs into single bands...')

    #     with rio.open(input_geotiff) as src:
    #         meta = src.meta.copy()

    #         for band in range(1, src.count + 1):
    #             data = src.read(band)

    #             output_filename = f"{geotiff_dir}/band________{band}.tif"
    #             print(output_filename)

    #             meta = src.meta.copy()
    #             meta.update({'count': 1})

    #             with rio.open(output_filename, 'w', **meta) as dst:
    #                 dst.write(data, 1)

    
    def find_empty_raster(self, **kwargs):
        """
        Finds geotiffs with no data
        Takes input_file
        """
        input_file = kwargs.get('input_file')

        with rio.open(input_file) as src:
            for i in range(1, src.count + 1):
                data = src.read(i)

                if not np.all(np.isnan(data)):
                    return False
        return True


    def create_sorted_outputs(self, **kwargs):
        """
        Function is prequisite for "sort outputs" folder.
        Function creates ASC and DSC folders for each polarization given.
        Takes folder_name and polarization
        """
        folder_name = kwargs.get('folder_name')
        polarization = kwargs.get('polarization')

        Path(folder_name).mkdir(exist_ok = True)
        output = output + folder_name
        Path(output).mkdir(exist_ok = True)

        for pol in polarization:
            Path(output + pol + '_ASC/').mkdir(exist_ok = True)
            Path(output + pol + '_DSC/').mkdir(exist_ok = True)
        return kwargs
        

    def sort_outputs(self, **kwargs):
        """
        Sorts geotiffs into folder based on polarizaton and orbital direction
        Requires "create_sorted_outputs" function to be run beforehand
        Takes input_file, output_path and polarization
        """
        input_file = kwargs.get('input_file')
        output_path = kwargs.get('output_path')
        polarization = kwargs.get('polarization')

        if not isinstance(polarization, list):
            polarization = [polarization]

        file_polarization = None
        for pol in polarization:
            if pol in input_file:  file_polarization = pol
        if file_polarization == None: 
            print(f'# ERROR: No polarization information in {input_file}!')
            return

        orbit_dir = None
        if '_ASC_' in input_file: orbit_dir = 'ASC'
        elif '_DSC_' in input_file: orbit_dir = 'DSC'
        if orbit_dir == None: print('# ERROR: No orbital direction information in file!')

        if None in (file_polarization, orbit_dir):
            Path(output_path + 'unsorted/').mkdir(exist_ok = True)
            shutil.copyfile(input_file, output_path + 'unsorted/')
            return

        sort_dir = output_path + file_polarization + '_' + orbit_dir + '/'
        sort_filename = sort_dir + os.path.basename(input_file)
        shutil.copyfile(input_file, sort_filename)
        return
    
    
    def get_reference_geotransform(self, **kwargs):
        """
        Function prequisite for using align_raster
        Function returns the geotransform from the largest file in dir
        Takes input_file_list
        """
        input_file_list = kwargs.get('input_file_list')
        
        reference_file = max(input_file_list, key=os.path.getsize)

        reference = gdal.Open(reference_file)
        reference_geotransform = reference.GetGeoTransform()
        reference = None

        arg_name = "reference_geotransform"
        kwargs[arg_name] = reference_geotransform

        return kwargs
    

    def align_raster(self, **kwargs):
        """
        Ensures pixels in a raster are aligned to same grid.
        Requires "get_reference_geotransform" function to be run beforehand
        Takes raster path, output_path, reference_geotransform
        """
        raster_path = kwargs.get('raster_path')
        output_path = kwargs.get('output_path')

        gdal.Warp(output_path,
                raster_path,
                xRes = kwargs.get('reference_geotransform')[1],
                yRes = -kwargs.get('reference_geotransform')[5],
                targetAlignedPixels = True,
                resampleAlg = gdal.GRA_NearestNeighbour
                )
        shutil.move(output_path, raster_path)
        return
                    

gdal.UseExceptions()
