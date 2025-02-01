#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import timeit

# Setup code
setup_code = """
import autorino.check as arochk
import autorino.common as arocmn

p = "/home/psakicki/aaa_FOURBI/OVSM/%Y/%j/rinex"
eporng = arocmn.EpochRange("2025-01-01", "2025-01-15")
chk = arochk.CheckGnss(inp_dir=p, site={'site_id': 'MLM000MTQ'}, epoch_range=eporng)
chk.guess_local_rnx(io="inp")
chk.check_local_files(io="inp")
"""

# Time analyze_rnxs
time_analyze_rnxs = timeit.timeit("chk.analyze_rnxs()", setup=setup_code, number=10)
print(f"Time for analyze_rnxs: {time_analyze_rnxs} seconds")

# Time analyze_rnxs2
time_analyze_rnxs2 = timeit.timeit("chk.analyze_rnxs2()", setup=setup_code, number=10)
print(f"Time for analyze_rnxs2: {time_analyze_rnxs2} seconds")