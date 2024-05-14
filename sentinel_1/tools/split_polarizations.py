import os
import sys
import rasterio as rio
from rasterio.enums import Compression
from pathlib import Path

from sentinel_1.utils import Utils
from sentinel_1.tools.tif_tool import TifTool


class SplitPolarizations(TifTool):
    def __init__(self, input_dir, shape, polarization, crs, mosaic_orbits=False, output_dir=False, threads = 1):
        self.input_dir = input_dir
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = self.input_dir
        self.shape = shape
        self.polarization = polarization
        self.crs = crs
        self.threads = threads
        self.mosaic_orbits = mosaic_orbits

    def printer(self):
        print(f"## Splitting polarization bands...")

    def process_file(self, input_file):
        """
        Splits a file with multiple polarization bands into one file per
        band with copies of auxiliary bands.
        Takes output_dir, polarization and crs
        """

        def get_band_polarization(pol, data_bands):
            data_matches = []
            for i, band in enumerate(data_bands):
                if pol in band[1]:
                    data_matches.append((i + 1, pol))
            return data_matches
        
        data_bands = Utils.extract_from_metadata(input_file, 'data_bands')
        incidence_bands = Utils.extract_from_metadata(input_file, 'data_bands')
        orbit_direction = Utils.extract_from_metadata(input_file, 'data_bands')

        # Clipping file down here saves a lot of compute
        # WITH METADATA NOW BEING HANDLED BY THE TOOL, CLIPPING CAN BE OUTSOURCED.
        if not self.mosaic_orbits:
            Utils.clip_256_single(input_file, self.shape, self.crs)

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

            output_filenames = []
            for i, (data_index, data_band) in enumerate(selected_data_bands, start=1):
                band_info = data_band + "_" + orbit_direction
                filename = (
                    os.path.basename(input_file).replace(Path(input_file).suffix, "_")
                    + band_info
                    + "_band.tif"
                )
                output_filenames.append(filename)
                output_geotiff = os.path.join(self.output_dir, filename)

                with rio.open(output_geotiff, "w", **meta) as dst:
                    dst.write(src.read(data_index), 1)
                    dst.set_band_description(1, data_band)
                    dst.nodata = -9999

                    for i, (incidence_index, incidence_band) in enumerate(
                        incidence_bands, start=len(data_bands)
                    ):
                        dst.write(src.read(incidence_index), i)
                        dst.set_band_description(i, incidence_band)

        if self.input_dir == self.output_dir:
            os.remove(input_file)

        return output_filenames