#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 12/09/2024 11:11:20

@author: psakic
"""
import pandas as pd
import requests
import os
from datetime import datetime
from tqdm import tqdm
import re
import argparse

import autorino.common as arocmn
import autorino.download as arodwl

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger('autorino')
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def download_html_page(url_inp, output_file_inp):
    """
    Download a webpage and save its content to a file.

    Parameters
    ----------
    url_inp : str
        The URL of the webpage to download.
    output_file_inp : str
        The file path where the content will be saved.

    Returns
    -------
    str or None
        The path to the downloaded file if successful, otherwise None.
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url_inp)

        # Check if the request was successful
        if response.status_code == 200:
            # Get the total file size
            total_size = int(response.headers.get("content-length", 0))
            # Write the content to the output file with a progress bar
            with open(output_file_inp, "wb") as file, tqdm(
                desc=output_file_inp,
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))
            logger.info(f"Page downloaded successfully and saved to {output_file_inp}")
            return output_file_inp
        else:
            logger.info(f"Failed to download page. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        logger.info(f"An error occurred: {e}")
        return None

# Example usage


def extract_trimble_filelist(
    html_files, pattern=r".{4}______[0-9]{12}A\.T02", output_csv_dir=None
):
    """
    Extract the list of Trimble files from an HTML file.

    Parameters
    ----------
    html_files : list or str
        The path to the HTML files. If a single file is provided, it should be a string.
    pattern : str, optional
        The regex pattern to match the Trimble files. Default is ".{4}______[0-9]{12}A\.T02".
    output_csv_dir : str, optional
        The directory where the CSV files will be saved. If None, CSV files will not be saved. Default is None.

    Returns
    -------
    list
        A list of Trimble files extracted from the HTML file.
    """

    if isinstance(html_files, str):
        html_files = [html_files]

    t02_stk = []
    for html_file in html_files:
        linelis = open(html_file).readlines()

        r_stk = []

        for l in linelis:
            # DSD0______202405010000A.T02
            r = re.search(pattern, l)
            if r:
                rok = r
                r_stk.append(rok.group(0))

        if output_csv_dir and len(r_stk) > 0:
            output_csv = os.path.join(
                output_csv_dir, os.path.basename(html_file).replace(".html", ".csv")
            )
            df = pd.DataFrame(sorted(list(set(r_stk))))
            df[1] = df[0].str.extract("(2[0-9]{7})").apply(pd.to_datetime)
            df.to_csv(output_csv, index=False, header=False)
            logger.info(f"Trimble file list saved to {output_csv}")

        t02_stk = t02_stk + sorted(list(set(r_stk)))

    t02_stk = sorted(list(set(t02_stk)))
    return t02_stk

def trimble_filelist_html(
    site,
    hostname,
    output_dir,
    start_date,
    end_date,
    period="1M",
    structure="download/Internal/%Y%m",
    force=False
):

    eporng = arocmn.EpochRange(start_date, end_date, period, round_method="none")
    output_paths_ok = []
    for curr_date in eporng.eporng_list():
        url = str(os.path.join('http://', hostname, curr_date.strftime(structure)))

        #output_path_ini = os.path.join(output_dir, os.path.basename(url))
        output_fnam_ok = site + "_" + os.path.basename(url) + ".html"
        output_path_ok = str(os.path.join(output_dir, output_fnam_ok))

        if not force and os.path.exists(output_path_ok):
            logger.info(f"File {output_path_ok} already exists. Skipping download.")
            output_paths_ok.append(output_path_ok)
        else:
            logger.info(f"Downloading page from {url}")
            output_path_out = arodwl.download_http(url, output_dir)
            if output_path_out:
                os.rename(output_path_out, output_path_ok)
                output_paths_ok.append(output_path_ok)

        if output_path_ok:
            extract_trimble_filelist(output_path_ok, output_csv_dir=output_dir)


