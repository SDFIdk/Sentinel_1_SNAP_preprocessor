import zipfile
from osgeo import gdal, osr
import os
import sys
import geopandas as gpd
import numpy as np
import rasterio as rio
from pathlib import Path
import glob
import shutil
import uuid
import pyproj
import tempfile

class Utils(object):
    def __init__(self):
        self.test = 'test'

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

    gdal.PushErrorHandler(gdal_error_handler)
    gdal.UseExceptions()

        
    def file_list_from_dir(directory, extensions, accept_no_files = False):
        """
        Returns file content of dir with given extension.
        If given a list of extensions, the function will whatever yields any files firt
        under assumption that the folder will only contain one type of files.
        """
        if not isinstance(extensions, list): extensions = [extensions]

        for extension in extensions:
            if not extension.startswith('*'): extension = '*' + extension

            file_list = glob.glob(directory + extension)
            if file_list: break

        if not accept_no_files: 
            assert len(file_list) != 0, (
                f'## No {str(extensions)} files in {directory}!'
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


    def remove_folder(folder):
        shutil.rmtree(folder)


#-----------------------------BELOW: MOVE TO SEPERATE FILES-----------------------------
    

    def shape_to_geojson(input_file, **kwargs):
        """
        Converts a shape to geoJSON
        Takes output_file and shape
        """
        shape = kwargs['shape']
        output_file = kwargs['output_file']

        shp_file = gpd.read_file(shape)
        geojson = output_file + str(uuid.uuid4()) + '.geojson'
        shp_file.to_file(geojson, driver='GeoJSON')
        return geojson


    # def extract_polarization_band(input_file, **kwargs):
    #     """
    #     Splits a netcdf into constituent bands depending depending on polarization
    #     Used for NetCDF
    #     Takes input_file, output_dir and polarization 
    #     """
    #     output_dir = kwargs['output_dir']
    #     polarization = kwargs['polarization']

    #     extension = Path(input_file).suffix
    #     input_dataset = gdal.Open(input_file, gdal.GA_ReadOnly)

    #     for subdataset in input_dataset.GetSubDatasets():

    #         subdataset_name, _ = subdataset
    #         band = gdal.Open(subdataset_name)
    #         metadata = band.GetMetadata()

    #         orbit = metadata['/Metadata_Group/Abstracted_Metadata/NC_GLOBAL#PASS']

    #         if orbit == 'ASCENDING': orbit_direction = 'ASC'
    #         elif orbit == 'DESCENDING': orbit_direction = 'DSC'
    #         else: 
    #             raise Exception('# Orbital direction not found in NetCDF metadata')

    #         for pol in polarization:
    #             if '_' + pol in subdataset_name:
    #                 band_type = pol
    #                 break
    #         assert band_type, (
    #             '# Polarization not found in NetCDF metadata'
    #         )

    #         for key, value in metadata.items():
    #             if 'srsName' in key: 
    #                 _, _, crs = value.partition('#')
    #                 crs = f'EPSG:{crs}'
    #                 break
    #         assert crs, (
    #             '# CRS not found in NetCDF metadata'
    #         )
    #         srs = osr.SpatialReference()
    #         srs.ImportFromEPSG(int(crs.split(':')[1]))

    #         translate_options = gdal.TranslateOptions(
    #             format = "GTiff",
    #             options = ["TILED=YES", "COMPRESS=LZW"],
    #             outputType = gdal.GDT_Float32,
    #             outputSRS=srs.ExportToWkt()
    #         )

    #         band_info = band_type + '_' + orbit_direction
            
    #         filename = os.path.basename(input_file).replace(extension, '_') + band_info + "_band.tif"
    #         output_geotiff = os.path.join(output_dir, filename)
            
    #         gdal.Translate(output_geotiff, band, options=translate_options)

    #     input_dataset = None        
    #     return
    

    def extract_polarization_band_incidence(input_file, **kwargs):
        """
        Splits a netcdf into constituent bands depending depending on polarization and 
        adds incidence angle bands to each polarization
        Used for NetCDF
        Takes output_dir and polarization 
        """
        def get_orbital_direction(input_file, metadata):
            orbit = metadata['/Metadata_Group/Abstracted_Metadata/NC_GLOBAL#PASS']

            if orbit == 'ASCENDING': orbit_direction = 'ASC'
            elif orbit == 'DESCENDING': orbit_direction = 'DSC'
            else: 
                raise Exception(f'# Orbital direction not found in {input_file} metadata')
            return orbit_direction
        
        def get_band_polarization(input_file, polarization, subdataset_name):
            for pol in polarization:
                if '_' + pol in subdataset_name:
                    band_type = pol
                    break
            assert band_type, (
                f'# Polarization not found in {input_file} metadata'
            )
            return band_type

        def get_srs(input_file, metadata):
            for key, value in metadata.items():
                if 'srsName' in key: 
                    _, _, crs = value.partition('#')
                    crs = f'EPSG:{crs}'
                    break
            assert crs, (
                f'# CRS not found in {input_file} metadata'
            )
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(int(crs.split(':')[1]))
            return srs

        output_dir = kwargs['output_dir']
        polarization = kwargs['polarization']

        gdal_dataset = gdal.Open(input_file, gdal.GA_ReadOnly)

        data_bands = []
        incidence_bands = []
        for subdataset in gdal_dataset.GetSubDatasets():
            if 'Intensity' in subdataset[1]:
                data_bands.append(subdataset)
            elif 'Angle' in subdataset[1]:
                incidence_bands.append(subdataset)
            else: raise Exception(f'# Band type not found in {gdal_dataset} metadata label')

        for subdataset in data_bands:
            band = gdal.Open(subdataset[0])
            metadata = band.GetMetadata()

            orbit_direction = get_orbital_direction(input_file, metadata)
            band_type = get_band_polarization(input_file, polarization, subdataset[0])
            srs = get_srs(input_file, metadata)

            band_info = band_type + '_' + orbit_direction
            filename = os.path.basename(input_file).replace(Path(input_file).suffix, '_') + band_info + "_band.tif"
            output_geotiff = os.path.join(output_dir, filename)

            vrt_options = gdal.BuildVRTOptions(resolution="highest", separate=True)
            band_paths = [subdataset[0] for subdataset in [subdataset] + incidence_bands]
            temp_vrt_path = os.path.join(output_dir, "temp_" + filename.replace(".tif", ".vrt"))

            vrt = gdal.BuildVRT(temp_vrt_path, band_paths, options=vrt_options)

            translate_options = gdal.TranslateOptions(
                format="GTiff",
                options=["TILED=YES", "COMPRESS=LZW"],
                outputType=gdal.GDT_Float32,
                outputSRS=srs.ExportToWkt()
            )

            gdal.Translate(output_geotiff, vrt, options=translate_options)
            vrt = None
            os.remove(temp_vrt_path)

        # for subdataset in gdal_dataset.GetSubDatasets():

        #     subdataset_name, _ = subdataset
        #     band = gdal.Open(subdataset_name)
        #     metadata = band.GetMetadata()

        #     orbit_direction = get_orbital_direction(input_file, metadata)
        #     band_type = get_band_polarization(input_file, polarization, subdataset_name)
        #     srs = get_srs(input_file, metadata)

        #     band_info = band_type + '_' + orbit_direction
        #     filename = os.path.basename(input_file).replace(Path(input_file).suffix, '_') + band_info + "_band.tif"
        #     output_geotiff = os.path.join(output_dir, filename)
            
        #     translate_options = gdal.TranslateOptions(
        #         format = "GTiff",
        #         options = ["TILED=YES", "COMPRESS=LZW"],
        #         outputType = gdal.GDT_Float32,
        #         outputSRS=srs.ExportToWkt()
        #     )

        #     gdal.Translate(output_geotiff, band, options=translate_options)
        # gdal_dataset = None        
        # return


    def remove_empty(input_file, **kwargs):
        """
        Finds geotiffs with no data and deletes them. Outputs none
        Used for geotiffs
        """
        with rio.open(input_file) as src:
            for i in range(1, src.count + 1):
                data = src.read(i)

                if np.all(np.isnan(data)):
                    os.remove(input_file)
        return 


    def unzip_data_to_dir(input_file, **kwargs):
        """
        Outputs content of zipfile to randomly named folder.
        Used for SAFE files
        """

        unzipped_safe = 'tmp/' + str(uuid.uuid4()) + '/'
        Path(unzipped_safe).mkdir(exist_ok = True)
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(unzipped_safe)
        
        return unzipped_safe
    
    
    def crs_warp(input_file, **kwargs):
        """
        Warps a raster to a new crs
        Takes crs 
        """
        crs = kwargs['crs']
        gdal_dataset = gdal.Open(input_file)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        output_file = str(uuid.uuid4()) + '.tif'

        options = gdal.WarpOptions(format = "GTiff", dstSRS = crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)     
        gdal.Warp(output_file, gdal_dataset, options = options)
        shutil.move(output_file, input_file)


    def TEST_crs_warp(input_file, **kwargs):
        """
        NEW THING USING tempfile AND GDAL CONTEXT MANAGER
        Warps a raster to a new CRS.
        Takes crs.
        """
        crs = kwargs['crs']

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_file = os.path.join(temp_dir, os.path.basename(input_file))

            with gdal.Open(input_file) as gdal_dataset:
                geotransform = gdal_dataset.GetGeoTransform()
                x_res = geotransform[1]
                y_res = -geotransform[5]

                options = gdal.WarpOptions(format="GTiff", dstSRS=crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)
                gdal.Warp(temp_output_file, gdal_dataset, options=options)

            shutil.move(temp_output_file, input_file)


    def change_raster_resolution(input_file, **kwargs):
        """
        Resamples a raster to a new resolution
        Takes x_size and y_size
        """
        x_size = kwargs['x_size']
        y_size = kwargs['y_size']

        gdal_dataset = gdal.Open(input_file)

        output_file = str(uuid.uuid4()) + '.tif'

        warp_options = gdal.WarpOptions(xRes=x_size, yRes=y_size, resampleAlg='near', format='GTiff')
        output_raster = gdal.Warp(output_file, gdal_dataset, options=warp_options)
        gdal_dataset = None
        output_raster = None

        shutil.move(output_file, input_file)


    # GDAL CONTEXT MANAGER EXPERIMENT
    # def NEW_change_raster_resolution(input_file, **kwargs):
    #     """
    #     Resamples a raster to a new resolution
    #     Takes input_file, x_size and y_size
    #     """
    #     x_size = kwargs['x_size']
    #     y_size = kwargs['y_size']

    #     with tempfile.TemporaryDirectory() as temp_file:
    #         with gdal.Open(input_file) as gdal_dataset:

    #             warp_options = gdal.WarpOptions(xRes=x_size, yRes=y_size, resampleAlg='near', format='GTiff')
    #             input_file = gdal.Warp(temp_file, gdal_dataset, options=warp_options)


    def split_polarizations(input_file, **kwargs):
        """
        Splits a multiband geotiff into seperate files with single bands
        MAY NOT BE NEEDED, DEPENDS ENTIRELY ON HOW SNAP EXECUTOR EVOLVES
        Takes input_file and polarization
        """
        polarization = kwargs['polarization']
        input_dir = kwargs['input_dir']

        with rio.open(input_file) as src:
            meta = src.meta.copy()

            for band in range(1, src.count + 1):
                data = src.read(band)

                output_filename = f"{input_dir}/band_{band}.tif"

                meta = src.meta.copy()
                meta.update({'count': 1})

                with rio.open(output_filename, 'w', **meta) as dst:
                    dst.write(data, 1)


    def create_sorted_outputs(input_file, **kwargs):
        """
        Function is prequisite for "sort outputs" folder.
        Function creates ASC and DSC folders for each polarization given.
        Takes output_path and polarization
        """
        output_path = kwargs['output_path']
        polarization = kwargs['polarization']

        Path(output_path).mkdir(exist_ok = True)

        for pol in polarization:
            Path(output_path + pol + '_ASC/').mkdir(exist_ok = True)
            Path(output_path + pol + '_DSC/').mkdir(exist_ok = True)
        return kwargs
        

    def sort_output(input_file, **kwargs):
        """
        Sorts geotiffs into folder based on polarizaton and orbital direction
        Requires "create_sorted_outputs" function to be run beforehand
        Takes output_path and polarization
        """
        output_path = kwargs['output_path']
        polarization = kwargs['polarization']

        if not isinstance(polarization, list):
            polarization = [polarization]

        file_polarization = None
        for pol in polarization:
            if pol in input_file:  file_polarization = pol
        if not file_polarization: print(f'# ERROR: No polarization information in {input_file}!')

        orbit_dir = None
        if '_ASC_' in input_file: orbit_dir = 'ASC'
        elif '_DSC_' in input_file: orbit_dir = 'DSC'
        if not orbit_dir: print(f'# ERROR: No orbital direction information in {input_file}!')

        if None in (file_polarization, orbit_dir):
            Path(output_path + 'unsorted/').mkdir(exist_ok = True)
            shutil.copyfile(input_file, output_path + 'unsorted/')
            return

        sort_dir = output_path + file_polarization + '_' + orbit_dir + '/'
        sort_filename = sort_dir + os.path.basename(input_file)
        shutil.copyfile(input_file, sort_filename)
        return
    
    
    def get_reference_geotransform(input_file, **kwargs):
        """
        Function prequisite for using align_raster
        Function returns the geotransform from the largest file in dir
        """
        input_dir = kwargs['input_dir']

        input_file_list = Utils.file_list_from_dir(input_dir, '*.tif')
        reference_file = max(input_file_list, key = os.path.getsize)

        reference = gdal.Open(reference_file)
        reference_geotransform = reference.GetGeoTransform()
        reference = None

        arg_name = "reference_geotransform"
        kwargs[arg_name] = reference_geotransform

        return kwargs
    
    
    def align_raster(input_file, **kwargs):
        """
        Ensures pixels in a raster are aligned to same grid.
        Requires "get_reference_geotransform" function to be run beforehand
        Takes reference_geotransform
        """
        reference_geotransform = kwargs['reference_geotransform']

        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp_file:
            tmp_file_path = tmp_file.name  # Get the temporary file path

        gdal.Warp(tmp_file_path,
                    input_file,
                    xRes=reference_geotransform[1],
                    yRes=-reference_geotransform[5],
                    targetAlignedPixels=True,
                    resampleAlg=gdal.GRA_NearestNeighbour)
        
        shutil.move(tmp_file_path, input_file)
        return


    def copy_dir(input_file, **kwargs):
        """
        Creates a copy of the directory given to it to a given location
        Takes file and copy_dir
        """
        copy_dir = kwargs['copy_dir']

        Utils.check_create_folder(copy_dir)

        copy_file = copy_dir + os.path.basename(input_file)
        shutil.copyfile(input_file, copy_file)
        print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')


    def trimmer_256(input_file, **kwargs):
        """
        Trims a dataset to a resolution divisible by 256
        """

        dataset =  gdal.Open(input_file)

        original_width = dataset.RasterXSize
        original_height = dataset.RasterYSize

        new_width = (original_width // 256) * 256
        new_height = (original_height // 256) * 256

        if new_width == original_width and new_height == original_height:
            return
        else:
            # with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp:
            #     temp_output_path = tmp.name
            temp_output_path = 'tmp.tif'
            driver = gdal.GetDriverByName('GTiff')
            out_dataset = driver.Create(temp_output_path, new_width, new_height, dataset.RasterCount,
                                        dataset.GetRasterBand(1).DataType)
            out_dataset.SetGeoTransform(dataset.GetGeoTransform())
            out_dataset.SetProjection(dataset.GetProjection())

            for i in range(dataset.RasterCount):
                in_band = dataset.GetRasterBand(i+1)
                out_band = out_dataset.GetRasterBand(i+1)

                data = in_band.ReadAsArray(0, 0, new_width, new_height)
                out_band.WriteArray(data)
        dataset = None
        out_dataset = None
        out_band = None

        shutil.move(temp_output_path, input_file)


    def convert_unit(input_file, **kwargs):
        """
        Converts units from raw backscatter to decibel or "power transform". 
        True zero_max will cap values of non linear at zero.
        Takes source_unit, desitnation_unit and zero_max
        """
        source_unit = kwargs['source_unit']
        destination_unit = kwargs['destination_unit']
        try: zero_max = kwargs['destination_unit']
        except: zero_max = False

        def only_zero_max_conversion(geotiff):
            with rio.open(geotiff, "r+") as src:
                dataset = src.read(1)
                zero_max_func(dataset)
                src.write(dataset, 1)
            return


        def zero_max_func(dataset):
            dataset[dataset > 0] = 0
            return dataset


        def no_op(geotiff, zero_max=False):
            return geotiff


        def generic_transform(dataset_in, equation, zero_max=False):
            dataset_out = equation(dataset_in)
            if zero_max:
                dataset_out = zero_max_func(dataset_out)
            return dataset_out


        source_to_linear = {
            "decibel": lambda a: 10.0 ** (a / 10.0),
            "power": lambda a: a**10,
            "linear": no_op,
        }
        linear_to_dest = {
            "decibel": lambda a: 10.0 * np.log10(a),
            "power": lambda a: a**0.1,
            "linear": no_op,
        }

        np.seterr(divide = 'ignore')

        if source_unit == destination_unit and zero_max:
            assert source_unit != "linear", "## Cannot set linear values to zero!"
            only_zero_max_conversion(input_file)
            return

        zero_max_out = False
        if zero_max and source_unit == "linear":
            zero_max_out = True
        zero_max_in = False
        if zero_max and destination_unit == "linear":
            zero_max_in = True

        with rio.open(input_file, "r+") as src:
            dataset = src.read(1)
            dataset = generic_transform(
                dataset, source_to_linear[source_unit], zero_max_in
            )
            dataset = generic_transform(
                dataset, linear_to_dest[destination_unit], zero_max_out
            )
            src.write(dataset, 1)


    # def TEST_FUNK(input_file, **kwargs):
    #     """
    #     TEST FUNCTION
    #     Takes test_var
    #     """
    #     test_var = kwargs['test_var']


    #     print(input_file)
    #     print(kwargs)
    #     print('------')

    #     # for arg in kwargs: 
    #     #     print(arg)
    #     for k, v in kwargs.items(): 
    #         print("%s = %s" % (k, v))

    #     sys.exit()

gdal.UseExceptions()
