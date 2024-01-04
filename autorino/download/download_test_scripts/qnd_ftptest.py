from autorino import download as arodl
from autorino import configread as arocfg


sta_user="***REMOVED***"
sta_pass="***REMOVED***"

outdir_use="/home/sysop/workflow_tests/download_tests"

rmot_file='ftp://10.10.4.52/Internal/202312/BOMG202312310000A.T02'

arodl.download_file_ftp(rmot_file,
                        outdir_use,
                        sta_user,
                        sta_pass)
