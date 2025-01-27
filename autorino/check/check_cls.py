#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 09:35:53

@author: psakic
"""

import autorino.handle as arohdl


class CheckGnss(arohdl.HandleGnss):
    def __init__(
        self,
        out_dir=None,
        tmp_dir=None,
        log_dir=None,
        inp_dir=None,
        inp_file_regex=None,
        epoch_range=None,
        site=None,
        session=None,
        options=None,
        metadata=None,
    ):

        super().__init__(
            out_dir=out_dir,
            tmp_dir=tmp_dir,
            log_dir=log_dir,
            inp_dir=inp_dir,
            inp_file_regex=inp_file_regex,
            epoch_range=epoch_range,
            site=site,
            session=session,
            options=options,
            metadata=metadata,
        )



