from cdsetool.query import query_features, shape_to_wkt
from cdsetool.credentials import Credentials
from cdsetool.download import download_features
from cdsetool.monitor import StatusMonitor
from sentinel_1.utils import Utils

from pathlib import Path
import sys
import os
from datetime import datetime
from collections import Counter

class StdLogger:
    """
    A logger that logs messages to stdout.
    """

    def debug(self, msg, *args, **kwargs):
        """
        Log a debug message to stdout.
        """
        print(f"DEBUG: {msg.format(*args, **kwargs)}")

    def error(self, msg, *args, **kwargs):
        """
        Log an error message to stdout.
        """
        print(f"ERROR: {msg.format(*args, **kwargs)}")

    def info(self, msg, *args, **kwargs):
        """
        Log an info message to stdout.
        """
        print(f"INFO: {msg.format(*args, **kwargs)}")

    def warning(self, msg, *args, **kwargs):
        """
        Log a warning message to stdout.
        """
        print(f"WARNING: {msg.format(*args, **kwargs)}")

class Downloader:
    @property
    def sentinel_1_safe_dir(self):
        return os.path.join(self.working_dir, "sentinel_1", "safe")

    @property
    def sentinel_2_safe_dir(self):
        # return os.path.join(self.working_dir, "sentinel_2", "safe")

        #TEMPORARY WORKAROUND
        return os.path.join("sentinel_2_temp_dir/", "sentinel_2", "safe")        

    def __init__(self, **kwargs):
        self.start_date = kwargs["start_date"]
        self.end_date = kwargs["end_date"]
        self.working_dir = kwargs["working_dir"]

        self.tmp_shape_dir = os.path.join(self.working_dir, 'tmp_shp')
        self.shape = Utils.shape_to_crs(
            kwargs["shape"], 
            self.tmp_shape_dir,
            target_crs = 'EPSG:4326'
            )

        self.verbose = kwargs.get("verbose", False)
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

        if self.verbose:
            datelist = []
            for feature in features:
                datelist.append(feature['properties']['startDate'])
            self.count_dates_by_month(datelist)

        assert (
            len(features) != 0
        ), f"## No Sentinel-1 data available between {self.start_date} and {self.end_date}!"

        print(f"## {len(features)} Sentinel-1 products will be acquired")
        self.download_features(features, self.sentinel_1_safe_dir)
        
        Utils.safer_remove(self.tmp_shape_dir)

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
                    #"monitor": StatusMonitor(),
                    "credentials": Credentials(),
                    "logger": StdLogger()
                },
            )
        )

    def count_dates_by_month(self, dates):

        date_objects = [datetime.strptime(date.split('T')[0], "%Y-%m-%d") for date in dates]            
        month_year = [(date.year, date.month) for date in date_objects]
        month_counts = Counter(month_year)
        
        print('# Data available for dates:')
        for (year, month), count in sorted(month_counts.items()):
            print(f"{year}-{month:02d}: {count} files")