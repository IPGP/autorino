from rinexmod.classes import RinexFile
from rinexmod.api import core_fcts
from rinexmod.api import rinexmod_main
from geodezyx import utils, conv
import subprocess
import os
import hatanaka
import shutil

sl_dir = "/home/sysop/DonneesTemporaires_GNSS/sitelogs"
p = "/home/sysop/DonneesTemporaires_GNSS/rinex15m/enriched/"
l = utils.find_recursive(p, "*d.gz")
dir_out_main = "/home/sysop/autorino_workflow/RNX2to4_wrk_tmp"
dir_out_uncmp =  dir_out_main + "/010_UNCMP"
dir_out_gfzrnx = dir_out_main + "/020_RNX4_gfzrnx"
dir_out_obsok = dir_out_main + "/030_RNX4_obsOK"
dir_out_rnxmod = dir_out_main + "/040_RNX4_rinexmoded"
dir_out_final = dir_out_main + "/050_RNX4_final"

utils.create_dir(dir_out_main)
utils.create_dir(dir_out_uncmp)
utils.create_dir(dir_out_gfzrnx)
utils.create_dir(dir_out_obsok)
utils.create_dir(dir_out_rnxmod)

for f in l:

    print(f)

    bn = os.path.basename(f)
    t = conv.rinexname2dt(f)
    dir_out_final_doy_site = os.path.join(dir_out_final, t.strftime("%Y"), t.strftime("%j"), bn[:4] + "00REU")
    bn_final_theo = conv.statname_dt2rinexname_long(bn[:4], t, country="REU", file_period="15M", data_freq="01S")

    if os.path.exists(os.path.join(dir_out_final_doy_site, bn_final_theo)):
        print(f"File {bn_final_theo} already exists in {dir_out_final_doy_site}, skipping.")
        continue


    ##### HATANAKA DECOMPRESSION
    try:
        hatanaka.decompress_on_disk(f)
    except Exception as e:
        print(f"Error decompressing {f}: {e}")
        continue
    bn_uncmp = bn.replace("d.gz", "o")
    dn = os.path.dirname(f)
    f_uncmp0 = os.path.join(str(dn),
                           str(bn_uncmp))
    f_uncmp = os.path.join(str(dir_out_uncmp),
                           str(bn_uncmp))
    if not os.path.exists(f_uncmp):
        shutil.move(f_uncmp0,dir_out_uncmp)


    bn_rnx3 = conv.statname_dt2rinexname_long(bn[:4],t)
    f_rnx3 = os.path.join(str(dir_out_gfzrnx), str(bn_rnx3))

    #### GFZRNX CONVERSION
    cmd = ["/home/sakic/SOFTWARE/GFZRNX/GFZRNX",
             "-finp",
             f_uncmp,
             "-vo 4",
             "-f",
             "-fout " + f_rnx3]

    print(" ".join(cmd))
    subprocess.call(" ".join(cmd), shell=True)

    #### RINEXMOD ADVANCED FOR OBSERVATION MAPPING
    r = RinexFile(f_rnx3)
    r.mod_sys_obs_types(core_fcts.map_sys_obs(r.get_sys_obs_types()[0],
                                              core_fcts.map_sys_obs_dic_default('SEPT POLARX5')))
    r.clean_translation_comments(True, True)
    f_obsok = r.write_to_path(dir_out_obsok)
    os.remove(f_rnx3)

    #### RINEXMOD "CLASSIC"
    sl = utils.find_recursive(sl_dir, bn[:4].lower() + "*" )[0]
    f_rnxmoded = rinexmod_main.rinexmod(f_obsok,
                                        dir_out_rnxmod,
                                        sitelog=sl,
                                        remove=True,
                                        verbose=False)

    #### FINAL SORT
    bn_rnxmoded = os.path.basename(f_rnxmoded)
    utils.create_dir(dir_out_final_doy_site)
    if not os.path.exists(os.path.join(dir_out_final_doy_site, bn_rnxmoded)):
        shutil.move(f_rnxmoded, dir_out_final_doy_site)
