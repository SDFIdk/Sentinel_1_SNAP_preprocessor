from osgeo import gdal
import sys
import os
import rasterio as rio
# from rasterio.merge import merge
# from rasterio.windows import from_bounds
# import shutil
# import tifffile
import xml.etree.ElementTree as ET
from sentinel_1.tools.tif_tool import TifTool
import glob

gdal.UseExceptions()

class MosaicOrbits(TifTool):
    def __init__(self, input_dir, threads = 1):
        self.input_dir = input_dir
        self.threads = threads

    def printer(self):
        print(f"## Mosaicing files with common orbits..")

    def process_file(self):
        """
        Combines images from the same orbit on within the same day into a single image
        """

        def build_metadata_dict(input_dir):
            orbit_dict = {}
            for geotiff in glob.glob(input_dir + '/*.tif'):
                geotiff_name = os.path.basename(geotiff)
                
                key = geotiff_name[49:55]

                if key in orbit_dict:
                    orbit_dict[key].append(geotiff)
                else:
                    orbit_dict[key] = [geotiff]

            return orbit_dict
        
        def rename_output(output_file):
            return os.path.splitext(output_file)[0] + '_ORBIT_MOSAIC' + os.path.splitext(output_file)[1]
        
        def combine_common_orbits(orbit_dict):
            for orbit_number, common_orbit_files in orbit_dict.items():
                output_file = rename_output(common_orbit_files[0])  
                
                if len(common_orbit_files) == 1: 
                    os.rename(common_orbit_files[0], output_file)
                else:
                    mosaic_large_geotiffs(common_orbit_files, output_file)

        def band_names_from_metadata(input_file):

            #EXTRACT BAND NAMES FROM METADATA
            with rio.open(input_file, 'r') as src:
                metadata = src.tags()

                band_names = metadata['data_bands'] | metadata['incidence_bands']
                breakpoint()

            return band_names
        
        
        # def reintegrate_snap_xml(output_file, metadata_xml):
        #     """
        #     Write XML content to custom tag 65000 in a TIFF file.
        #     """

        #     with tifffile.TiffWriter(output_file, append=True) as tif:
        #         tif.write(extra_tags=[(65000, 's', 0, metadata_xml, True)])


        def mosaic_large_geotiffs(file_list, output_file):
            """
            Mosaic large GeoTIFF files by processing them in chunks.

            Parameters:
            - file_list (list): List of file paths to be merged.
            - output_file (str): Path to the output mosaic file.
            """

            band_names = band_names_from_metadata(file_list[-1])
            
            with rio.open(file_list[0]) as src:
                meta = src.meta.copy()

            with rio.open(output_file, 'w', **meta) as dst:
                breakpoint()
                print(output_file)
                for idx, file in enumerate(file_list):
                    with rio.open(file) as src:

                        for ji, window in src.block_windows(1):
                            data = src.read(window=window)

                            dst.write(data, window=window)

                    print(f"Processed and added {file} to mosaic.")
                for bidx, name in enumerate(band_names, 1):
                    dst.set_band_description(bidx, name)
                dst.no_data = -9999

            # reintegrate_snap_xml(output_file, metadata_xml)

            print(f"Mosaic created: {output_file}")

        def delete_original_files(original_geotiffs):
            for geotiff in original_geotiffs: 
                try: os.remove(geotiff)
                except: continue

        original_geotiffs = glob.glob(self.input_dir + '/*.tif')

        orbit_dict = build_metadata_dict(self.input_dir)
        
        combine_common_orbits(orbit_dict)

        delete_original_files(original_geotiffs)