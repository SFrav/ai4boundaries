import os
import urllib.error
import urllib.request
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import time

# URL of the dataset
BASE_URL = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/AI4BOUNDARIES/'


def download_file(url, dst_path):
    """
    Download files to disk

    :param url: URL of the file to download
    :param dst_path: File location on disk after download
    """
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode='wb') as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        print(f"Failed to download {url}: {e}")


def download_ai4boundaries(dir, sensor='All', country='All'):
    """
    Download AI4boundaries dataset with specified sensor and country.
    
    :param dir: Path to directory where to save the data.
    :param sensor: Sensor type ('All', 'ortho', 's2').
    :param country: Country code ('All', 'AT', 'ES', 'FR', 'LU', 'NL', 'SE', 'SI').
    """
    # Validate inputs
    valid_sensors = ['All', 'ortho', 's2']
    valid_countries = ['All', 'AT', 'ES', 'FR', 'LU', 'NL', 'SE', 'SI']

    if sensor not in valid_sensors:
        raise ValueError(f"Invalid sensor value. Choose from {valid_sensors}")
    if country not in valid_countries:
        raise ValueError(f"Invalid country value. Choose from {valid_countries}")

    # Adjust the base URL according to sensor and country
    urls = []
    url_fns = []

    # Logic for selecting the appropriate URL based on the sensor and country
    if sensor == 'All' and country == 'All':
        url = BASE_URL
        urls.append(url)
    elif sensor == 'ortho':
        if country == 'All':
            url = f"{BASE_URL}orthophoto/"
            urls.append(url)
        else:
            url_images = f"{BASE_URL}orthophoto/images/{country}/"
            url_masks = f"{BASE_URL}orthophoto/masks/{country}/"
            urls.extend([url_images, url_masks])
    elif sensor == 's2':
        if country == 'All':
            url = f"{BASE_URL}sentinel2/"
            urls.append(url)
        else:
            url_images = f"{BASE_URL}sentinel2/images/{country}/"
            url_masks = f"{BASE_URL}sentinel2/masks/{country}/"
            urls.extend([url_images, url_masks])

    def scrape(site):
        """
        Recursively scrape a website to get all file URLs.
        :param site: The URL to start scraping from
        """
        # getting the request from url
        r = requests.get(site)
        # converting the text
        s = BeautifulSoup(r.text, "html.parser")

        for i in s.find_all("a"):
            href = i.attrs['href']
            if href.endswith("/"):
                subsite = site + href
                if subsite not in urls:
                    urls.append(subsite)
                    # calling it self
                    scrape(subsite)
            if href.endswith("tif") | href.endswith("nc"):
                url_fn_ = site + href
                url_fns.append(url_fn_)

    print('Scraping data')
    for url in urls:
        scrape(url)

    # Create the directory structure based on the scraped URLs
    print('Creating folder architecture')
    if dir.endswith('/'):
        subdirs = [i.replace(BASE_URL, dir) for i in urls if not i.endswith('DRLL/')]
    else:
        subdirs = [i.replace(BASE_URL, dir + '/') for i in urls if not i.endswith('DRLL/')]

    subdirs = [subdir.replace('DRLL/', '') for subdir in subdirs if not 'ftp' in subdir]

    for subdir in subdirs:
        Path(subdir).mkdir(parents=True, exist_ok=True)

    # Download the files
    failed_fns = []
    print('Downloading data')
    for url_fn in tqdm(url_fns):
        if dir.endswith('/'):
            fn = url_fn.replace(BASE_URL, dir)
        else:
            fn = url_fn.replace(BASE_URL, dir + '/')
        try:
            download_file(url_fn, fn)
        except:
            time.sleep(20)
            failed_fns.append(url_fn)

    # Reprocessing failed downloads
    print('Reprocessing failed downloads')
    for url_fn in tqdm(failed_fns):
        if dir.endswith('/'):
            fn = url_fn.replace(BASE_URL, dir)
        else:
            fn = url_fn.replace(BASE_URL, dir + '/')
        try:
            download_file(url_fn, fn)
        except:
            continue

    print('Download finished!')
    print('Cite the data set:')
    print('d\'Andrimont, R., Claverie, M., Kempeneers, P., Muraro, D., Yordanov, M., Peressutti, D., Batič, M., '
          'and Waldner, F.: AI4Boundaries: an open AI-ready dataset to map field boundaries with Sentinel-2 and aerial '
          'photography, Earth Syst. Sci. Data Discuss. [preprint], '
          'https://doi.org/10.5194/essd-2022-298, in review, 2022.')


if __name__ == '__main__':
    out_dir = r'C:/Users/ai4boundaries'
    sensor = 'All'
    country = 'All'
    download_ai4boundaries(out_dir, sensor, country)
