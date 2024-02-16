from cdsetool.query import query_features, shape_to_wkt
from cdsetool.credentials import Credentials
from cdsetool.download import download_features
from cdsetool.monitor import StatusMonitor
from datetime import date

from pathlib import Path
import sys
import os


class Downloader:
    @property
    def sentinel_1_safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_1", "safe")

    @property
    def sentinel_2_safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_2", "safe")

    def __init__(self, **kwargs):
        self.start_date = kwargs["start_date"]
        self.end_date = kwargs["end_date"]
        self.shape = kwargs["shape"]
        self.working_dir = kwargs["working_dir"]
        self.cloud_cover = kwargs.get("cloud_cover", "[0,100]").replace(" ", "")
        self.concurrency = kwargs.get("concurrency", 4)

        Path(self.sentinel_1_safe_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sentinel_2_safe_dir).mkdir(parents=True, exist_ok=True)

    def download_sentinel_1(self):
        features = query_features(
            "Sentinel1",
            {
                "startDate": self.start_date,
                "completionDate": self.end_date,
                "processingLevel": "LEVEL1",
                "sensorMode": "IW",
                "productType": "IW_GRDH_1S",
                "geometry": shape_to_wkt(self.shape),
            },
        )
        assert (
            len(features) != 0
        ), f"## No Sentinel-1 data available between {self.start_date} and {self.end_date}!"
        print(f"## {len(features)} Sentinel-1 products will be acquired")
        self.download_features(features, self.sentinel_1_safe_dir)

    def download_sentinel_2(self):
        features = query_features(
            "Sentinel2",
            {
                "startDate": self.start_date,
                "completionDate": self.end_date,
                "processingLevel": "S2MSI2A",
                "cloudCover": self.cloud_cover,
                "geometry": shape_to_wkt(self.shape),
            },
        )
        if len(features) == 0:
            print(
                f"## No Sentinel-2 data available between {self.start_date} and {self.end_date}!"
            )
            print("## Consider adjusting max cloud cover parameteres if possible.")
            return
        else:
            print(f"## {len(features)} Sentinel-2 products will be acquired")
            self.download_features(features, self.sentinel_2_safe_dir)

    def download_features(self, features, output):
        list(
            download_features(
                features,
                output,
                {
                    "concurrency": self.concurrency,
                    "monitor": StatusMonitor(),
                    "credentials": Credentials(),
                },
            )
        )
