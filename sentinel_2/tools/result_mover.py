import os
import shutil
from sentinel_2.tools.s2_tools import S2TifTool

class ResultMover(S2TifTool):

    def __init__(self, input_dir, sentinel_2_output, threads = 1):
        self.input_dir = input_dir
        self.sentinel_2_output = sentinel_2_output

    def printer():
        print("## Moving results to output dir...")

    def process_file(self, input_file):

        destination = os.path.join(self.sentinel_2_output, os.path.basename(input_file))

        shutil.move(input_file, destination)
