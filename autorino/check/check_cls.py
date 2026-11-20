#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 09:35:53

@author: psakic
"""
import pandas as pd
import numpy as np

import autorino.handle as arohdl
#import autorino.check as arochk
#import rinexmod.classes as rimo_cls
#import tqdm


class CheckGnss(arohdl.HandleGnss):
    def __init__(
        self,
        **kwargs
    ):
        """
        Initialize a CheckGnss object.

        This constructor initializes a CheckGnss object, which is used for checking
        and analyzing RINEX files. It inherits from the HandleGnss class.

        Parameters
        ----------
        **kwargs : keyword arguments
            Additional keyword arguments passed to the parent HandleGnss class.
            Common parameters include:
            - out_dir : str, optional - The output directory for the check results.
            - tmp_dir : str, optional - The temporary directory for intermediate files.
            - log_dir : str, optional - The directory for log files.
            - inp_dir : str, optional - The input directory for RINEX files.
            - inp_file_regex : str, optional - Regular expression pattern for input files.
            - epoch_range : EpochRange, optional - The range of epochs to be checked.
            - site : dict, optional - Information about the site.
            - session : dict, optional - Information about the session.
            - options : dict, optional - Additional options for the check operation.
            - metadata : str or list, optional - Metadata for the check operation.
        """
        super().__init__(**kwargs)

        self.table_stats = pd.DataFrame()

