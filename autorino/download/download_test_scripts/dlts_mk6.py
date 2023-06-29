import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as ardl
import yaml


###########################################################################################

def session_request_from_configfile(configfile_path):
    
    Y1 = yaml.safe_load(open(configfile_path))
    
    Ystation = Y1["station"]

    protocol = Ystation["access"]["protocol"]
    hostname = Ystation["access"]["hostname"]
    sta_user = Ystation["access"]["login"]
    sta_pass = Ystation["access"]["password"]
    site = Ystation["site"]    
    
    
    Ysession_list = Ystation["sessions_list"]
    
    Sess_stk, Req_stk = [], []
    
    for Yses0 in Ysession_list:
        ########### Session
        Yses = Yses0["session"]
        name   = Yses["name"]
        
        session_period = Yses["file_period"]
        remote_dir     = Yses["remote_dir"]
        remote_fname   = Yses["remote_fname"]    
        
        Sess = ardl.SessionGnss(
        name = name,
        protocol = protocol,
        remote_dir=remote_dir,
        hostname=hostname,
        sta_user=sta_user,
        sta_pass=sta_pass,
        site=site,
        session_period=session_period,
        remote_fname=remote_fname)
        
        Sess_stk.append(Sess)
        
        ############ Request
        Yreq = Yses0["request"]
        Ydownload = Yreq["download"]
        
        output_dir_parent = Ydownload["output_dir_parent"] 
        output_dir_struture = Ydownload["output_dir_structure"] 
        output_path = os.path.join(output_dir_parent,output_dir_struture)

        ##### Epoch Range
        Yepochrange = Ydownload["epoch_range"]        
        Range = ardl.EpochRange(Yepochrange["epoch1"],
                                Yepochrange["epoch2"],
                                session_period)
        
        Req = ardl.RequestGnss(Sess,Range,output_path)
        
        Req_stk.append(Req)
        
    if len(Sess_stk) < 2:
        return Sess_stk[0], Req_stk[0]
    else:
        return Sess_stk, Req_stk

pconfig = "/home/gps/tests_pierres/autorino/configfiles/proto_config_HOUE_03a.yml"
pconfig = "/home/gps/tests_pierres/autorino/configfiles/proto_config_PSA1_03a.yml"

Y1 = yaml.safe_load(open(pconfig))

SESlist, REQlist = session_request_from_configfile(pconfig)
REQ = REQlist[1]
#REQ = REQlist

#L = REQ.ask_remote_files()
L = REQ.guess_remote_local_files(guess_local=1)
L = REQ.check_local_files()
L = REQ.invalidate_small_local_files()

print(REQ.req_table.to_string())

REQ.download_remote_files()
print(REQ.req_table.to_string())
