from concurrent.futures import ProcessPoolExecutor, wait
from sentinel_1.utils import Utils
from sentinel_1.snap_xml_handler import UpdataMetadata
import rasterio as rio


class TifTool:
    """
    Tool category for Sentinel-1 GeoTIFFs derived from SNAP
    """
    def __init__(self, input_dir, threads, crs):
        self.input_dir = input_dir
        self.threads = threads

    def setup(self):
        pass

    def printer(self):
        pass

    def loop(self, input_file):
        self.metadata = UpdataMetadata.copy_metadata(input_file)
        self.process_file(input_file)
        UpdataMetadata.paste_metadata(input_file, self.metadata)

    def process_file(self, input_object):
        pass

    def teardown(self):
        pass

    def files(self):
        if 'safe' in self.input_dir:
            return Utils.file_list_from_dir(self.input_dir, "*.zip")
        else:
            return Utils.file_list_from_dir(self.input_dir, "*.tif")

    def run(self):
        self.printer()
        self.setup()
        if self.threads > 1:
            self._run_parallel()
        else:
            self._run_linear()

        self.teardown()

    def _run_parallel(self):
        files = self.files()

        with ProcessPoolExecutor(self.threads) as exc:
            futures = [exc.submit(self.process_file, input_file) for input_file in files]
            wait(futures)

    def _run_linear(self):
        files = self.files()
        for input_file in files:
            self.process_file(input_file)