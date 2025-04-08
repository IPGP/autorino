#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 12:17:17 2024

@author: psakicki
"""

#### Import star style


import autorino.general as arogen

# import autorino.workflow as arowkf
# import autorino.epochrange as aroepo
# import autorino.session as aroses
import autorino.handle as arohdl

epo = arogen.create_dummy_epochrange()
ses = arogen.create_dummy_session()

H = arohdl.HandleGnss(ses, epo, out_dir="/tmp/")

H.guess_local_files()
wrkflw_grp_lis = H.group_epochs()

W = wrkflw_grp_lis[0]
W.updt_eporng_tab()

# for t in H.table.groupby('epoch_rnd'):
#     print(t)

_ = H.print_table()
