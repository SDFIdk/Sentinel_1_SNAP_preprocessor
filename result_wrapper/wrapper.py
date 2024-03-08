import os
import py7zr
import sys
import shutil
from glob import glob
import pathlib

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

        if os.path.splitext(self.shape)[1] == '.zip':
            shape_data = self.shape
        else: 
            shape_data = pathlib.PurePath(self.shape).parent.name
            shutil.make_archive(os.path.join(self.result_dir, shape_data), 'zip', pathlib.PurePath(self.shape).parent)

        all_results = glob(self.result_dir + '/*/')
        all_results.append(os.path.join(self.result_dir, shape_data+'.zip'))

        result_zip = os.path.join(self.result_dir, os.path.basename(self.working_dir) + '.7z')
        with py7zr.SevenZipFile(result_zip, 'w') as archive:
            for item in all_results:
                if os.path.isdir(item):
                    base_dir_name = os.path.basename(os.path.normpath(item))
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(base_dir_name, os.path.relpath(file_path, start=item))
                            archive.write(file_path, arcname)
                            print(file)
                else:
                    archive.write(item, os.path.basename(item))

        for item in all_results:
            try:
                shutil.rmtree(item)
            except:
                os.remove(item)
            finally:
                raise Exception(f"## Cannot remove {item}!")