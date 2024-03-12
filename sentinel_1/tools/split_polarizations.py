import os
import sys
import rasterio as rio
import tifffile
import xml.etree.ElementTree as ET
from rasterio.enums import Compression
from pathlib import Path

from sentinel_1.tools.tool import Tool
from sentinel_1.tools.clip_256 import Clip256


class SplitPolarizations(Tool):
    def __init__(self, input_dir, shape, polarization, crs, output_dir=False):
        self.input_dir = input_dir
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = self.input_dir
        self.shape = shape
        self.polarization = polarization
        self.crs = crs

    def printer(self):
        print(f"## Splitting polarization bands...")

    def loop(self, input_file):
        """
        Splits a file with multiple polarization bands into one file per
        band with copies of auxiliary bands.
        Takes output_dir, polarization and crs
        """

        def get_orbital_direction(input_file, tag=65000):
            # 65000 is standard geotiff tag for metadata xml
            with tifffile.TiffFile(input_file) as tif:
                tree = tif.pages[0].tags[tag].value
                assert (
                    tree
                ), f"# {input_file} does not contain SNAP assocaited metadata!"

                root = ET.fromstring(tree)
                metadata = root.findall("Dataset_Sources")[0][0][0]

                for mdattr in metadata.findall("MDATTR"):
                    if not mdattr.get("name") == "PASS":
                        continue

                    orbital_direction = mdattr.text
                    if orbital_direction == "ASCENDING":
                        return "ASC"
                    elif orbital_direction == "DESCENDING":
                        return "DSC"

        def get_band_polarization(pol, data_bands):
            data_matches = []
            for i, band in enumerate(data_bands):
                if pol in band[1]:
                    data_matches.append((i + 1, pol))
            return data_matches

        def band_names_from_snap_geotiff(input_file, tag=65000):
            # 65000 is standard geotiff tag for metadata xml
            with tifffile.TiffFile(input_file) as tif:
                tree = tif.pages[0].tags[tag].value
                assert (
                    tree
                ), f"# {input_file} does not contain SNAP assocaited metadata!"

                root = ET.fromstring(tree)
                data_access = root.findall("Data_Access")[0]

                data_bands = []
                incidence_bands = []
                for i, data_file in enumerate(data_access.findall("Data_File")):
                    band_name = data_file.find("DATA_FILE_PATH").get("href")
                    band_name = os.path.splitext(os.path.basename(band_name))[0]

                    if "VV" in band_name or "VH" in band_name:
                        data_bands.append((i + 1, band_name))
                    else:
                        incidence_bands.append((i + 1, band_name))

            return data_bands, incidence_bands, root

        data_bands, incidence_bands, metadata_xml = band_names_from_snap_geotiff(
            input_file
        )
        orbit_direction = get_orbital_direction(input_file)

        # Clipping file down here saves a lot of compute
        Clip256(input_file, self.shape, self.crs, single_file=True).run()

        with rio.open(input_file) as src:
            meta = src.meta.copy()
            meta.update(
                count=src.count - (len(self.polarization) - 1),
                compress=Compression.lzw.name,
            )

            selected_data_bands = [
                item
                for pol in self.polarization
                for item in get_band_polarization(pol, data_bands)
            ]

            for i, (data_index, data_band) in enumerate(selected_data_bands, start=1):
                band_info = data_band + "_" + orbit_direction
                filename = (
                    os.path.basename(input_file).replace(Path(input_file).suffix, "_")
                    + band_info
                    + "_band.tif"
                )
                output_geotiff = os.path.join(self.output_dir, filename)

                with rio.open(output_geotiff, "w", **meta) as dst:
                    dst.write(src.read(data_index), 1)
                    dst.set_band_description(1, data_band)
                    dst.update_tags(ns="xml", **{"TIFFTAG_XMLPACKET": metadata_xml})
                    dst.nodata = -9999

                    for i, (incidence_index, incidence_band) in enumerate(
                        incidence_bands, start=2
                    ):
                        dst.write(src.read(incidence_index), i)
                        dst.set_band_description(i, incidence_band)

        if self.input_dir == self.output_dir:
            os.remove(input_file)
