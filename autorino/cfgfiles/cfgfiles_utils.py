#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 14/01/2025 15:23:34

@author: psakic
"""

import re
import jinja2
import geodezyx
import os
import datetime

def feed_template(template_full_path, df_values, outdir, out_fname_prefix):
    """
    Feed a Jinja2 template with values from a DataFrame and write the results to files.

    Parameters
    ----------
    template_full_path : str
        The full path to the Jinja2 template file.
    df_values : pandas.DataFrame
        DataFrame containing the values to feed into the template.
    outdir : str
        The directory where the output files will be written.
    out_fname_prefix : str
        The prefix for the output file names.

    Returns
    -------
    None
    """
    template_dir = os.path.dirname(template_full_path)
    template_fname = os.path.basename(template_full_path)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=template_dir),
                             trim_blocks=True,
                             lstrip_blocks=True)
    template = env.get_template(template_fname)

    for irow, row in df_values.iterrows():
        print(irow, "#########################################")
        print(row)
        result = template.render(row.to_dict(),
                                 current_time=datetime.datetime.utcnow(),
                                 #trim_blocks=True,
                                 #lstrip_blocks=True
                                 )

        if "outdirsub" in df_values.columns:
            outdirsub = os.path.join(outdir, row["outdirsub"])
        else:
            outdirsub = outdir

        geodezyx.utils.create_dir(outdirsub)

        outfile = os.path.join(outdirsub, out_fname_prefix + row["site"] + ".yml")
        print(outfile)
        fout = open(outfile, "w+")
        fout.write(result)
        fout.close()


def teqc_args_spliter(linp):
    """
    Split TEQC arguments into a dictionary.
    For OVSG legacy configuration files only.

    Parameters
    ----------
    linp : str
        The string containing TEQC arguments.

    Returns
    -------
    dict
        A dictionary where keys are TEQC options and values are their corresponding arguments.
    """
    d = dict()
    ls = linp.split()
    v = []
    k = "void"
    d[k] = ""
    for e in ls:
        if re.match(r"-O\..*", e):
            print(e)
            k = e
            d[k] = ""
        else:
            d[k] = d[k] + " " + e

    del d["void"]

    return d
