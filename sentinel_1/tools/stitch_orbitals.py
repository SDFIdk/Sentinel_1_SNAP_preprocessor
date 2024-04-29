from osgeo import gdal
import sys
import re
import os
import rasterio as rio
from rasterio.merge import merge
from rasterio.windows import from_bounds
import shutil
import tifffile
import xml.etree.ElementTree as ET


import glob
# from sentinel_1.utils import Utils

gdal.UseExceptions()

class StitchOrbitals():
    def __init__(self, geotiff_dir):
        self.geotiff_dir = geotiff_dir

    def run(self):
        """
        Combines images from the same orbit on within the same day into a single image
        """

        def build_metadata_dict(geotiff_dir):
            orbit_dict = {}
            for geotiff in glob.glob(geotiff_dir + '/*.tif'):
                geotiff_name = os.path.basename(geotiff)

                if '_COMBINED_ORBIT' in geotiff_name: continue
                
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
                    # create_pyramids(output_file)

        def extract_metadata_xml(input_file, tag=65000):
            # 65000 is standard geotiff tag for SNAP metadata xml
            with tifffile.TiffFile(input_file) as tif:
                tree = tif.pages[0].tags[tag].value
                assert (
                    tree
                ), f"# {input_file} does not contain SNAP assocaited metadata!"

                root = ET.fromstring(tree)
                data_access = root.findall("Data_Access")[0]

                band_names = []
                for i, data_file in enumerate(data_access.findall("Data_File")):
                    band_name = data_file.find("DATA_FILE_PATH").get("href")
                    band_names.append(os.path.splitext(os.path.basename(band_name))[0])

            return band_names, root       

        def mosaic_large_geotiffs(file_list, output_file):
            """
            Mosaic large GeoTIFF files by processing them in chunks.

            Parameters:
            - file_list (list): List of file paths to be merged.
            - output_file (str): Path to the output mosaic file.
            """

            band_names, metadata_xml = extract_metadata_xml(file_list[-1])
            
            with rio.open(file_list[0]) as src:
                meta = src.meta.copy()

            with rio.open(output_file, 'w', **meta) as dst:
                print(output_file)
                for idx, file in enumerate(file_list):
                    with rio.open(file) as src:

                        for ji, window in src.block_windows(1):
                            data = src.read(window=window)

                            dst.write(data, window=window)

                    print(f"Processed and added {file} to mosaic.")
                dst.update_tags(ns="xml", **{"TIFFT G_XMLPACKET": metadata_xml})
                for bidx, name in enumerate(band_names, 1):
                    dst.set_band_description(bidx, name)
                dst.no_data = -9999

            print(f"Mosaic created: {output_file}")

        def create_pyramids(file_path):
            """
            Create pyramids for a GeoTIFF file using GDAL Python bindings.
            """
            ds = gdal.Open(file_path, gdal.GA_Update)
            
            if ds is None:
                print("Failed to open file.")
                return
            
            ds.BuildOverviews("average", [2, 4, 8, 16, 32])
            ds = None
            print(f'# Pyramids created for {file_path}')

        def delete_original_files(original_geotiffs):
            for geotiff in original_geotiffs: 
                try: os.remove(geotiff)
                except: continue

        original_geotiffs = glob.glob(self.geotiff_dir + '/*.tif')

        orbit_dict = build_metadata_dict(self.geotiff_dir)
        
        combine_common_orbits(orbit_dict)

        delete_original_files(original_geotiffs)