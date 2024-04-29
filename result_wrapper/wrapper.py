import os
import py7zr
import sys
import shutil
from glob import glob
import pathlib
import time


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

    def safe_remove(self, path):
        """Attempt to remove a file or directory with retries for locked files."""
        max_retries = 5
        retry_delay = 1  # one second

        for _ in range(max_retries):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
                break
            except Exception as e:
                print(f"# Warning: failed to delete {path} due to {e}")
                time.sleep(retry_delay)
        else:
            print(f"# Error: could not delete {path} after {max_retries} retries.")

    def wrap_results(self):

        print('## Wrapping results...')
        if os.path.splitext(self.shape)[1] == ".zip":
            shape_data = self.shape
        else:
            shape_data = pathlib.PurePath(self.shape).parent.name
            shutil.make_archive(
                os.path.join(self.result_dir, shape_data),
                "zip",
                pathlib.PurePath(self.shape).parent,
            )

        all_results = glob(self.result_dir + "/*/")
        all_results.append(os.path.join(self.result_dir, shape_data + ".zip"))

        result_zip = os.path.join(
            self.result_dir, os.path.basename(os.path.normpath(self.working_dir)) + ".7z"
        )

        with py7zr.SevenZipFile(result_zip, "w") as archive:
            for item in all_results:
                if os.path.isdir(item):
                    base_dir_name = os.path.basename(os.path.normpath(item))
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(
                                base_dir_name, os.path.relpath(file_path, start=item)
                            )
                            archive.write(file_path, arcname)
                else:
                    archive.write(item, os.path.basename(item))

        for item in all_results:
            self.safe_remove(item)