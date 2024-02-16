import tempfile
import shutil
from osgeo import gdal

gdal.UseExceptions()


class AlignRaster(Tool):
    def run(self, input_file, **kwargs):
        """
        Ensures pixels in a raster are aligned to same grid.
        Requires "get_reference_geotransform" function to be run beforehand
        Takes reference_geotransform
        """
        reference_geotransform = kwargs["reference_geotransform"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
            tmp_file_path = tmp_file.name  # Get the temporary file path

        gdal.Warp(
            tmp_file_path,
            input_file,
            xRes=reference_geotransform[1],
            yRes=-reference_geotransform[5],
            targetAlignedPixels=True,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )

        shutil.move(tmp_file_path, input_file)
