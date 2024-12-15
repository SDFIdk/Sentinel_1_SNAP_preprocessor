import os


from sentinel_2.tools.s2_tools import S2SAFETool
from sentinel_2.s2_utils import Utils
from sentinel_2.tiff_generator import TiffGenerator

class SAFEToGeotiff(S2SAFETool):
    def __init__(self, input_dir, output_dir, max_cloud, shape = None, threads = 1):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.max_cloud = max_cloud
        self.shape = shape
        self.threads = threads


    def printer():
        print("## Converting SAFE to geotiff...")


    def process_file(self, input_file):

        os.makedirs(self.output_dir, exist_ok=True)

        if not self.shape:
            TiffGenerator.generate_geotiffs(input_file, self.output_dir)
            return
        
        if Utils.aoi_cloud_cover(input_file, self.shape) >= self.max_cloud:
            print(f"# {input_file} exceeded {self.max_cloud} %, skipping...")

        TiffGenerator.generate_geotiffs(input_file, self.output_dir)