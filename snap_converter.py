import subprocess
import os
from glob import glob

class SNAP_preprocessor(object):
    def safe_preprocessing(safe_directory, graph_xml, output_directory, gpt_path):
        print('## Applying SNAP pre-processing stack to SAFE files...')

        safe_files = glob(safe_directory + '*.zip')

        for i, safe_file in enumerate(safe_files):
            print('# ' + str(i+1) + ' / ' + str(len(safe_files)), end = '\r')

            netcdf_output_name = os.path.basename(safe_file).replace('.zip', '.nc')
            netcdf_output_path = os.path.join(output_directory, netcdf_output_name)

            SNAP_preprocessor.run_gpt(graph_xml, gpt_path, safe_file, netcdf_output_path)

    def run_gpt(graph_xml, gpt_path, safe_file, netcdf_output_path):

        cmd = [gpt_path, graph_xml, '-PinputSafeFile=' + safe_file, '-PoutputSafeFile=' + netcdf_output_path]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"GPT exited with an error:\n{stderr.decode()}")
        else:
            print(stdout.decode())