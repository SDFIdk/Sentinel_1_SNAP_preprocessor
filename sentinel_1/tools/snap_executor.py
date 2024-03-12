import os
import sys
from sentinel_1.tools.tool import Tool
import subprocess
import xml.etree.ElementTree as ET

class SnapExecutor(Tool):
    """
    This script applies a SNAP graph onto a directorys worth of files
    Takes in input, output, SNAP graph and a path the the gpt.exe
    """

    def __init__(self, input_dir, output_dir, gpt_exe, graph_xml, input_ext='.zip', threads = 1):
        self.input_dir = input_dir
        self.gpt_exe = gpt_exe
        self.input_ext = input_ext
        self.output_dir = output_dir
        self.graph_xml = graph_xml
        #have to run this in serial from Tool's side, as SNAP handles it own multi processing 
        self.threads = 1
        self.gpt_threads = threads

    def setup(self):
        """
        Extrapolate output file extension from graph xml
        """
        
        #expected formats
        format_dict = {"GeoTIFF": ".tif", "NetCDF": ".nc"}

        root = ET.parse(self.graph_xml).getroot()

        for node in root.findall("node"):
            name = node.get("id")
            if name == "Write":
                params = node.find("parameters")
                format_element = params.find("formatName")
                format_name = format_element.text

                for format, ext in format_dict.items():
                    if format in format_name:
                        self.output_ext = ext
                        return
                raise Exception("## No Write node found! Check graph!")


    def loop(self, input_file):
        print(f"## Applying SNAP processing stack to {self.input_ext} files...")

        output_filename = os.path.basename(input_file).replace(
            self.input_ext, self.output_ext
        )
        output_path = os.path.join(self.output_dir, output_filename)
        cmd = [
            self.gpt_exe,
            self.graph_xml,
            "-PinputSafeFile=" + input_file,
            "-PoutputSafeFile=" + output_path,
            "-q", str(self.gpt_threads)  
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"GPT exited with an error:\n{stderr.decode()}")
        else:
            print(stdout.decode())