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
        all_results = [].append(
            glob(self.sentinel_1_files + "/"),
            glob(self.sentinel_2_files + "/"),
            self.shape,
        )

        print(all_results)

        output_name = os.path.join(
            self.result_dir, os.path.basename(self.working_dir) + ".7z"
        )

        print(output_name)

        with py7zr.SevenZipFile(output_name, "w") as archive:
            for data in all_results:
                archive.write(data)
