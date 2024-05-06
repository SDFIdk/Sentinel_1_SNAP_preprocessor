import os
import sys
import tifffile
import xml.etree.ElementTree as ET
import rasterio as rio

"""
Extracts data necessary for other tools and from the 65000 tag and 
stores them in a rasterio compatible way for easier inheritability 
between operations
"""


#store in tag snap_metadata in a single dict
#update dict with one function per entry

#given that split_polarization requires data for each band also, the function should then also
# have a second dict which stores band data??? Order, Name, Polarization VV/VH, Calibration Y/N, Incidence Y/N

class ExtractMetadata:
    def __init__(self, input_file):
        self.input_file = input_file
        self.metadata_dict = {}

    def get_snap_xml(self, input_file):
        """
        Extract metadata xml
        """

        # SNAP stores metadata in xml format in tag 65000
        tag = 65000

        with tifffile.TiffFile(input_file) as tif:
            tree = tif.pages[0].tags[tag].value
            assert (
                tree
            ), f"# {input_file} does not contain SNAP assocaited metadata!"

            self.snap_xml = tree

    def get_orbital_direction(self):
        """
        Orbital pass direction, necessary parameter for dataset splitting and labeling
        """

        root = ET.fromstring(self.snap_xml)
        metadata = root.findall("Dataset_Sources")[0][0][0]

        for mdattr in metadata.findall("MDATTR"):
            if not mdattr.get("name") == "PASS":
                continue

            orbital_direction = mdattr.text
            if orbital_direction == "ASCENDING":
                return "ASC"
            elif orbital_direction == "DESCENDING":
                return "DSC"
            
        self.metadata_dict['orbital_direction'] = orbital_direction

    def get_band_info(self):

        root = ET.fromstring(self.snap_xml)
        data_access = root.findall("Data_Access")[0]

        data_bands = []
        incidence_bands = []

        i = 1
        for data_file in data_access.findall("Data_File"):
            band_name = data_file.find("DATA_FILE_PATH").get("href")
            band_name = os.path.splitext(os.path.basename(band_name))[0]

            if "VV" in band_name or "VH" in band_name:
                data_bands.append((i , band_name))
                i += 1
            elif band_name == 'incidenceAngleFromEllipsoid':
                # HARD CODED CHECK FOR SPECIFIC INCIDENCE ANGLE, REQUIRED BY GEUS
                incidence_bands.append((i, band_name))
                i += 1

        self.metadata_dict['data_bands'] = data_bands
        self.metadata_dict['incidence_bands'] = incidence_bands
        
    def get_orbit_number(self):
        """
        Extracts orbit number for file name
        """

        self.metadata_dict['orbit_number'] = self.input_file[48:54]

    def write_metadata(self):

        with rio.open(self.input_file, 'r+') as src:

            metadata = src.tags()
            metadata.update(self.metadata_dict)

            # Optionally, you can also update tags per band if needed
            # dst.update_tags(1, **metadata)


    def run(self):
        self.snap_xml = self.get_snap_xml(self.input_file)

        self.get_orbital_direction()
        self.get_band_info()
        self.get_orbit_number()

        self.write_metadata()







