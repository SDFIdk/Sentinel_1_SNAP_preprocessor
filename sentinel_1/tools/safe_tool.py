from concurrent.futures import ProcessPoolExecutor, wait
from sentinel_1.utils import Utils
from sentinel_1.metadata_utils import ExtractSNAPMetadata


class SAFETool:
    """
    Tool category specifically for handling SAFE files
    """
    def __init__(self, input_dir, threads, crs):
        self.input_dir = input_dir
        self.threads = threads

    def setup(self):
        pass

    def printer(self):
        pass

    def loop(self, input_object):
        pass

    def teardown(self):
        pass

    def metadata_update(self, input_file):
        ExtractSNAPMetadata(input_file).run()

    def files(self):
        return Utils.file_list_from_dir(self.input_dir, "*.zip")

    def run(self):
        self.printer()
        self.setup()
        self._run_linear()

        self.teardown()

    def _run_linear(self):
        files = self.files()
        for input_file in files:
            output_file = self.loop(input_file)

            self.metadata_update(output_file)
            
            
