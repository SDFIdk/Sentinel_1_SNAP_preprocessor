import os
import shutil
import sys

from sentinel_1.tools.tif_tool import TifTool
from sentinel_1.utils import Utils


class CopyDir(TifTool):
    def __init__(self, input_dir, copy_dir, threads = 1):
        self.input_dir = input_dir
        self.copy_dir = copy_dir
        self.threads = threads


    def printer(self):
        print(f"## Copying rsaters...")

    def process_file(self, input_file):
        """
        Creates a copy of the directory given to it to a given location
        Takes file and copy_dir
        """

        Utils.check_create_folder(self.copy_dir)

        copy_file = self.copy_dir + os.path.basename(input_file)
        shutil.copyfile(input_file, copy_file)
