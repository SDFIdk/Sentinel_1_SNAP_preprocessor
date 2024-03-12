import subprocess
import xml.etree.ElementTree as ET
import os
import sys

from sentinel_1.utils import Utils


class SnapPreprocessor(object):


    def __init__(self, gpt_path):
        self.gpt = gpt_path

    def graph_processing(self, input_path, output_dir, graph_xml, input_ext=".zip"):
        print(f"## Applying SNAP processing stack to {input_ext} files...")

        input_files = Utils.file_list_from_dir(
            input_path, input_ext, accept_no_files=False
        )

        output_ext = self.extract_output_ext(graph_xml)

        for i, input_file in enumerate(input_files):
            print("# " + str(i + 1) + " / " + str(len(input_files)), end="\r")

            output_filename = os.path.basename(input_file).replace(
                input_ext, output_ext
            )
            output_path = os.path.join(output_dir, output_filename)

            self.run_gpt(graph_xml, self.gpt, input_file, output_path)

    def run_gpt(self, graph_xml, gpt_path, input_file, output_path):
        cmd = [
            gpt_path,
            graph_xml,
            "-PinputSafeFile=" + input_file,
            "-PoutputSafeFile=" + output_path,
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"GPT exited with an error:\n{stderr.decode()}")
        else:
            print(stdout.decode())

    def extract_output_ext(self, graph_xml):
        """
        Function looks for the field formatName in the Write node.
        This is specific to SNAP generated processing graphs
        """
