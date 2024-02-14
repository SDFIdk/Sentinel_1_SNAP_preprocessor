from osgeo import gdal
import os
import shutil
import uuid
from s1.utils import Utils


class AlignRaster(Tool):  # wont reconize Tool. Why?
    def run(self, input_file, **kwargs):
        tmp_dir = "/tmp/"  # TODO: make this configurable

        Utils.check_create_folder(tmp_dir)
        tmp_file = tmp_dir + str(uuid.uuid4()) + ".tif"

        gdal.Warp(
            tmp_file,
            input_file,
            xRes=self.reference_geotransform[1],
            yRes=-self.reference_geotransform[5],
            targetAlignedPixels=True,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        shutil.move(tmp_file, input_file)
