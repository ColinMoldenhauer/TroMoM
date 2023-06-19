import os
import json
import pandas as pd
import re
import requests


def smap_path(shortname, version, year, month, day):
    fpath_start = 'https://n5eil01u.ecs.nsidc.org/SMAP'
    url_path = f"{fpath_start}/{shortname}{version}/{year}.{month}.{day}/"
    return url_path


def get_most_recent_version(shortname):
    cmr_collections_url = 'https://cmr.earthdata.nasa.gov/search/collections.json'

    response = requests.get(cmr_collections_url, params={"short_name": shortname})
    results = json.loads(response.content)
    versions = [el['version_id'] for el in results['feed']['entry']]
    latest_version = max(versions)

    return f".{latest_version}"


def make_request(session, url):
    response = session.get(url)
    # If the response code is 401, we still need to authorize with earthdata.
    if response.status_code == 401:
        response = session.get(response.url)
    assert response.ok, 'Problem downloading data! Reason: {}'.format(response.reason)

    return response


def get_files(session, url_path):
    response = make_request(session, url_path)
    response_str = response.content.decode('utf-8')

    match = re.findall(r'href="(SMAP_L3_SM_P_E_\d{8}_R18290_\d{3}.h5)"><img', response_str)
    assert len(match) == 1, f"Response has {len(match)} file-like patterns, check multi-file case!"

    return match


# TODO: use AOI: probably ignore in download and use for "acquire" or smth
def download_smap_single_date(shortname, date, data_dir="data", version=None, verbose=True):
    credentials_smap = {
        "mail": "colin.moldenhauer@tum.de",
        "user": "TroMoM",
        "pwd": "jWrfPSxNh54DTZX"
    }
    version = version or get_most_recent_version(shortname)
    year, month, day = date.split("-")

    with requests.Session() as session:
        session.auth = (credentials_smap["user"], credentials_smap["pwd"])

        url_path = smap_path(shortname, version, year, month, day)
        if verbose: print(f"Downloading SMAP data for: {year}-{month}-{day} ({url_path})")

        file_names = get_files(session, url_path)
        for i, file_name_ in enumerate(file_names):
            if verbose: print(f"\tfile: {file_name_} [{i+1}/{len(file_names)}]")

            full_url = url_path + file_name_
            response = make_request(session, full_url)

            filepath = os.path.join(data_dir, "SMAP", file_name_)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            if verbose: print('\t*** SM data downloaded to: '+ filepath +' *** ')


def download_smap(shortname, AOI, dates):
    dates = [str(d_)[:10] for d_ in pd.date_range(*dates)]
    for date_ in dates:
        download_smap_single_date(shortname, date_)
