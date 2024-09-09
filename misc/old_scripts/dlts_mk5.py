import datetime as dt

from autorino import download as ardl

############################################################
# protocol = "http"
# hostname="http://gps-abd.terrain.ovsg.univ-ag.fr/"
# inp_dir_parent="download/Internal/%Y%m/"
# sta_user=""
# sta_pass=""

# protocol = "http"
# inp_dir_parent="download/Internal/%Y%m/"
# hostname="http://gps-dsd.terrain.ovsg.univ-ag.fr"
# sta_user=""
# sta_pass=""

# protocol = "http"
# inp_dir_parent="download/Internal/%Y%m/"
# hostname="http://195.83.190.74"
# sta_user=""
# sta_pass=""

# # HOUE
# protocol = "ftp"
# inp_dir_parent="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d"
# hostname="gps-houe.terrain.ovsg.univ-ag.fr"
# sta_user="root"
# sta_pass="ovsg13;:"



# AGAL
protocol = "http"
hostname="http://10.0.76.158"
remote_dir="download/Internal/%Y%m/"
remote_fname=""
sta_user=""
sta_pass=""
site4="AGAL"
session_period="01D"






# PSA1 Hourly
protocol = "http"
hostname="http://gps-psa.terrain.ovsg.univ-ag.fr"
remote_dir="download/Internal/%Y%m/"
remote_fname="<SITE4>______%Y%m%d%H%MB.T02"
sta_user=""
sta_pass=""
site4="PSA1"
session_period="01H"

# ABD0
protocol = "http"
hostname="http://gps-abd.terrain.ovsg.univ-ag.fr/"
remote_dir="download/Internal/%Y%m/"
remote_fname="<SITE4>______%Y%m%d%H%MA.T02"
sta_user=""
sta_pass=""
site4="ABD0"
session_period="01D"



#######' HOUE
protocol = "ftp"
hostname="gps-houe.terrain.ovsg.univ-ag.fr"
remote_dir="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d"
remote_fname="<SITE4>%j0.m00"
sta_user="root"
sta_pass="ovsg13;:"
site4="HOUE"
session_period="01D"


# PSA1
protocol = "http"
hostname="http://gps-psa.terrain.ovsg.univ-ag.fr"
remote_dir="download/Internal/%Y%m/"
remote_fname="<SITE4>______%Y%m%d%H%MA.T02"
sta_user=""
sta_pass=""
site4="PSA1"
session_period="01D"

###########################################################################################

SESS = ardl.SessionGnss(
name="toto",
protocol = protocol,
remote_dir=remote_dir,
hostname=hostname,
sta_user=sta_user,
sta_pass=sta_pass,
site=site4,
session_period=session_period,
remote_fname=remote_fname)

output_path = "/home/gps/tests_pierres/dltest/<SITE4>/%Y"

now = dt.datetime.now() - dt.timedelta(days=10)
epoch_interest = now - dt.timedelta(days=1)

DR = ardl.EpochRange(epoch_interest,now)

print(DR)

REQ = ardl.RequestGnss(SESS,DR,output_path)

#L = REQ.ask_remote_raw()
L = REQ.guess_remote_local_files(guess_local=1)
L = REQ.check_local_files()


print(REQ.req_table.to_string())

REQ.download_remote_files()
print(REQ.req_table.to_string())
