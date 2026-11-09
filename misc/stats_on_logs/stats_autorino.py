import pandas as pd
import tabulate
p = "/home/sakic/CODES/IPGP/autorino/download_logs_analysis_ovpf.csv"
df = pd.read_csv(p)

df["epoch_exec"] = pd.to_datetime(df["epoch_exec"])
df["epoch_srt"] = pd.to_datetime(df["epoch_srt"])

df["d_epoch"] = (df["epoch_exec"] - df["epoch_srt"]).dt.round("1D")

def do_stats(df_inp):
    dftt = df_inp[df_inp["ok_inp"] & df_inp["ok_out"]]
    df1 = dftt[dftt['d_epoch'] <= pd.Timedelta("1D")]
    df2 = dftt[(dftt['d_epoch'] > pd.Timedelta("1D")) & (dftt['d_epoch'] <= pd.Timedelta("2D"))]
    df3 = dftt[(dftt['d_epoch'] > pd.Timedelta("2D")) & (dftt['d_epoch'] <= pd.Timedelta("10D"))]
    df10 = dftt[dftt['d_epoch'] > pd.Timedelta("10D")]

    ntt = len(dftt)
    n1 = len(df1)
    n2 = len(df2)
    n3 = len(df3)
    n10 = len(df10)

    import numpy as np
    ratio1 = n1/ntt
    ratio2 = n2/ntt
    ratio3 = n3/ntt
    ratio10 = n10/ntt
    srat = lambda x: str(np.round(x *100,2)) + "%"

    exec = dftt.drop_duplicates("epoch_exec", keep="last")["exec_time"]

    exec_mean = str(np.round(np.mean(exec),2)) +"s"
    exec_median = str(np.round(np.nanmedian(exec),2)) +"s"
    exec_min = str(np.round(np.min(exec),2)) +"s"
    exec_max = str(np.round(np.max(exec),2)) +"s"

    outtup = (ntt, n1, n2 , n3, n10 ,
              srat(ratio1),
              srat(ratio1 + ratio2),
              srat(ratio1 + ratio2 + ratio3),
              srat(ratio10),
              exec_mean, exec_median, exec_min, exec_max)

    return outtup

tupall = do_stats(df)
tupall = [str(tup) for tup in tupall]

print("\n".join(tupall))

sitetupstk = []
for site, dfsite in df.groupby("site"):
    sitetup = (site,) + do_stats(dfsite)
    print(sitetup)
    sitetupstk.append(sitetup)

t = tabulate.tabulate(sitetupstk, tablefmt="latex")
#print(t.replace(r"\\", r"\\ \hline"))

print(t)



