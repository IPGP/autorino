import autorino
import datetime as dt

p = "/home/sakic/IPGP_WORK/OVS/GNSS_OVS/2607_GNSS_repet_OVSM/0320_OUT_flat"
psplice = "/home/sakic/IPGP_WORK/OVS/GNSS_OVS/2607_GNSS_repet_OVSM/0310_OUT_spliced/"
ptmp = "/home/sakic/IPGP_WORK/OVS/GNSS_OVS/2607_GNSS_repet_OVSM/0390_OUT_tmp/"

autorino.api.splice_rnx(p, psplice, ptmp,
                        epoch_srt=dt.datetime(2026,7,21),
                        epoch_end=dt.datetime(2026,8,3))