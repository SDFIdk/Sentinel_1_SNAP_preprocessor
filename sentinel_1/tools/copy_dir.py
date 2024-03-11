import os
import shutil
import sys

from sentinel_1.tools.tool import Tool
from sentinel_1.utils import Utils

class CopyDir(Tool):
    def __init__(self, input_dir, copy_dir):
        self.input_dir = input_dir
        self.copy_dir = copy_dir

    def loop(self, input_file):
        """
        Creates a copy of the directory given to it to a given location
        Takes file and copy_dir
        """

        Utils.check_create_folder(self.copy_dir)

        copy_file = self.copy_dir + os.path.basename(input_file)
        shutil.copyfile(input_file, copy_file)