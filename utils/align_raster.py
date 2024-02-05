from osgeo import gdal
import os
import shutil
import uuid

class AlignRaster(Tool):
    def __init__(self, input_dir=None):
        self.input_dir = input_dir
        self.reference_geotransform = None

    def setup(self):

        reference_file = max(input_file_list, key = os.path.getsize)

        with gdal.Open(reference_file) as reference:
            self.reference_geotransform = reference.GetGeoTransform()

    def loop(self, input_file):
        tmp_dir = '/tmp/' # TODO: make this configurable

        Utils.check_create_folder(tmp_dir)
        tmp_file = tmp_dir + str(uuid.uuid4()) + '.tif'

        gdal.Warp(
            tmp_file,
            input_file,
            xRes = self.reference_geotransform[1],
            yRes = -self.reference_geotransform[5],
            targetAlignedPixels = True,
            resampleAlg = gdal.GRA_NearestNeighbour
        )

        shutil.move(tmp_file, input_file)