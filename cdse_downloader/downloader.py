from cdsetool.query import query_features, shape_to_wkt
from cdsetool.credentials import Credentials
from cdsetool.download import download_features
from cdsetool.monitor import StatusMonitor
from datetime import date

import sys
import os

class Downloader:
    def __init__(self, **kwargs):
                
        self.start_date = kwargs['start_date']
        self.end_date = kwargs['end_date']
        self.shape = kwargs['shape']
        self.output = kwargs['safe_dir']
        self.cloud_cover = kwargs.get('cloud_cover', '[0,100]').replace(" ", "")
        self.concurrency = kwargs.get('concurrency', 4)

    def download_sentinel_1(self):
        features = query_features(
            "Sentinel1",
            {
                "startDate": self.start_date,
                "completionDate": self.completion_Date,
                "processingLevel": "LEVEL1",
                "sensorMode": "IW",
                "productType": "IW_GRDH_1S",
                "geometry": self.shape,
            }
        )
        download_features(features)


    def download_sentinel_2(self):
        features = query_features(
            "Sentinel2",
            {
                "startDate": self.start_date,
                "completionDate": self.completion_Date,
                "processingLevel": "S2MSI2A",
                "cloudCover": self.cloud_cover,
                "geometry": self.shape,
            },
        )
        
        download_features(features)


    def download_features(self, features):
        list(
            download_features(
                features,
                self.output,
                {
                    "concurrency": self.concurrency,
                    "monitor": StatusMonitor(),
                    "credentials": Credentials(),
                },
            )
        )