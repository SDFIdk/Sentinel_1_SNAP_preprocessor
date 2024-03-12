from osgeo import gdal
import shutil
import sys
from sentinel_1.tools.tool import Tool

gdal.UseExceptions()


class Trim256(Tool):
    def __init__(self, input_dir):
        self.input_dir = input_dir

    def printer(self):
        print(f"## Trimming to 256...")

    def loop(self, input_file):
        """
        Trims a dataset to a resolution divisible by 256
        """

        dataset = gdal.Open(input_file)

        original_width = dataset.RasterXSize
        original_height = dataset.RasterYSize

        new_width = (original_width // 256) * 256
        new_height = (original_height // 256) * 256

        if new_width == original_width and new_height == original_height:
            return
        else:
            temp_output_path = "tmp.tif"
            driver = gdal.GetDriverByName("GTiff")
            out_dataset = driver.Create(
                temp_output_path,
                new_width,
                new_height,
                dataset.RasterCount,
                dataset.GetRasterBand(1).DataType,
            )
            out_dataset.SetGeoTransform(dataset.GetGeoTransform())
            out_dataset.SetProjection(dataset.GetProjection())

            for i in range(dataset.RasterCount):
                in_band = dataset.GetRasterBand(i + 1)
                out_band = out_dataset.GetRasterBand(i + 1)

                data = in_band.ReadAsArray(0, 0, new_width, new_height)
                out_band.WriteArray(data)
        dataset = None
        out_dataset = None
        out_band = None

        shutil.move(temp_output_path, input_file)
