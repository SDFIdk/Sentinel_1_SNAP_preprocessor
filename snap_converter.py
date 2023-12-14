import subprocess
import os
from glob import glob
import xml.etree.ElementTree as ET
import sys

class SNAP_preprocessor(object):

    """
    This script applies a SNAP graph onto a directorys worth of files
    Takes in input, output, SNAP graph and a path the the gpt.exe
    """

    def __init__(self, gpt_path):
        self.gpt = gpt_path


    def graph_processing(self, input_path, output_dir, graph_xml, output_ext, input_ext = '.zip'):
        print(f'## Applying SNAP processing stack to {input_ext} files...')

        input_files = glob(input_path + f'*{input_ext}')

        # if input_path == output_path:
        #     output_path = ''

        # output_ext = self.extract_output_ext(graph_xml)
        # TODO parse graph xml to extract output extension for saving.

        for i, input_file in enumerate(input_files):
            print('# ' + str(i+1) + ' / ' + str(len(input_files)), end = '\r')

            output_filename = os.path.basename(input_file).replace(f'{input_ext}', f'{output_ext}')
            output_path = os.path.join(output_dir, output_filename)

            self.run_gpt(graph_xml, self.gpt, input_file, output_path)


    def run_gpt(self, graph_xml, gpt_path, input_file, output_path):

        cmd = [gpt_path, graph_xml, '-PinputSafeFile=' + input_file, '-PoutputSafeFile=' + output_path]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"GPT exited with an error:\n{stderr.decode()}")
        else:
            print(stdout.decode())


    # def extract_output_ext(self, graph_xml):
    #     tree = ET.parse(graph_xml)
    #     root = tree.getroot()

    #     format = None
    #     # print(list(root))
    #     print(root.findall('graph'))
    #     # print('a')
        
    #     value = tree.find('graph/node/parameters/formatName')
    #     print(value)
    #     import sys; sys.exit()


    #     for node in root.findall('graph'):
    #         print(node.find('operator').text)
    #         import sys; sys.exit()
    #         if not node.get('id') == 'Write':
    #             pass

    #         parameters = node.find('parameters')
    #         if not parameters:
    #             raise Exception('## SNAP Graph Write commponent broken, contains no parameters!')
            
    #         format_name = parameters.find('formatName')
    #         assert format_name, (
    #             'No specified format name in Write component! Specify in SNAP'
    #         )
    #         format = format_name.text
    #     if not format: raise Exception('## SNAP Graph contains no Write component!')

    #     output_ext = any(format in key for key in format_dict)
    #     print(output_ext)
    #     import sys; sys.exit()
    #     return(output_ext)
                
    #     print(ext_format)
    #     import sys; sys.exit()
    #     return None

format_dict = {
    "Geotiff": ".tif",
    "NetCDF": ".nc"
}   #expand with other SNAP write parameters according to need