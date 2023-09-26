# Import credentials
from creds import *
import requests
import sys
import netrc
import pandas as pd
import pprint
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import geopandas as gpd

def get_auth_from_netrc(url):
    info = netrc.netrc()
    auth = info.authenticators(url)

    if auth:
        login, _, password = auth
        return login, password
    else:
        return None, None

def get_keycloak():

    url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    username, password = get_auth_from_netrc(url)

    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
        }
    try:
        r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Keycloak token creation failed. Reponse from the server was: {r.json()}"
            )
    return r.json()["access_token"]

# def download_file(url, token, target_folder="."):
#     """Download a file from the given URL to the target folder."""
#     headers = {
#         "Authorization": f"Bearer {token}"  # Assuming token is a bearer token
#     }
#     response = requests.get(url, headers=headers, stream=True)
#     response.raise_for_status()

#     # Get file name from Content-Disposition header or URL
#     filename = os.path.join(target_folder, url.split("/")[-1])
#     with open(filename, 'wb') as file:
#         for chunk in response.iter_content(chunk_size=8192):
#             file.write(chunk)
#     return filename  # Return the filename indicating a successful download

def acquire_from_cdse(link, filename, token):
    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {token}'})

    response = session.get(link, allow_redirects=False)

    while response.status_code in (301, 302, 303, 307):
        url = response.headers['Location']
        response = session.get(url, allow_redirects=False)

        file = session.get(url, verify=False, allow_redirects=True)

    file_output = '/output' + filename

    with open(file_output, 'wb') as p:
        p.write(file.content)
    return

def convert_to_odata_polygon(shape):

    shape = gpd.read_file(shape).geometry[0]

    exterior = shape.exterior
    coordinates = list(exterior.coords)

    odata_str = "POLYGON((" + ", ".join(" ".join(map(str, coord)) for coord in coordinates) + "))"

    return odata_str

start_date = "2020-01-01"
end_date = "2020-05-01"
shape = "ribe_aoi/ribe_aoi.shp"

footprint = convert_to_odata_polygon(shape)

# Constants
collection = "Sentinel1"
sensor_mode = "IW"
processing_level = "LEVEL1"
product_type = "GRD"


#either raise limit or query in chunks, one week at a time
response = requests.get(f"https://catalogue.dataspace.copernicus.eu/resto/api/collections/{collection}/search.json?startDate={start_date}&completionDate={end_date}&geometry={footprint}&sensorMode={sensor_mode}&processingLevel={processing_level}&productType={product_type}")

json_response = response.json()

download_links = []
for feature in json_response.get("features", []):

    # pprint.pprint(feature)
    # sys.exit()

    link = feature.get("properties", {}).get("services", {}).get("download", {}).get("url")
    destination = feature.get("properties", {}).get("title")

    download_links.append((link, destination))


keycloak_token = get_keycloak()

for link, destination in download_links:
    acquire_from_cdse(link, destination, keycloak_token)



# keycloak_token = get_keycloak()
# num_workers = 5  # Adjust this based on your system and requirements
# with ThreadPoolExecutor(max_workers=num_workers) as executor:
#     futures = [executor.submit(download_file, link, keycloak_token) for link in download_links]
#     for future in as_completed(futures):
#         try:
#             filename = future.result()
#             print(f"Successfully downloaded {filename}")
#         except Exception as e:
#             print(f"Error downloading file. Reason: {e}")