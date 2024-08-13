from autorino import download as arodl

sta_user="***REMOVED***"
sta_pass="***REMOVED***"

outdir_use="/home/sysop/workflow_tests/download_tests"

rmot_file='ftp://***REMOVED***/Internal/202312/BOMG202312310000A.T02'

arodl.download_ftp(rmot_file,
                   outdir_use,
                   sta_user,
                   sta_pass)
