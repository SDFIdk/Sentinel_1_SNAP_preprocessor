import os
import zipfile
import py7zr
import sys
from glob import glob


class ResultWrapper:
    @property
    def sentinel_1_files(self):
        return os.path.join(self.working_dir, "sentinel_1")

    @property
    def sentinel_2_files(self):
        return os.path.join(self.working_dir, "sentinel_2")

    def __init__(self, **kwargs):
        self.working_dir = kwargs["working_dir"]
        self.shape = kwargs["shape"]
        self.result_dir = kwargs["result_dir"]

    def wrap_results(self):
        all_results = [
            glob(self.sentinel_1_files + "/")[0],
            glob(self.sentinel_2_files + "/")[0],
            self.shape,
        ]

        zip_name = self.working_dir
        if zip_name.endswith('/'): 
            zip_name = zip_name[:-1]
        zip_name = zip_name.split("/").pop() + ".7z"

        output_name = os.path.join(
            self.result_dir, zip_name
        )

        with py7zr.SevenZipFile(output_name, "w") as archive:
            for data in all_results:
                archive.write(data)