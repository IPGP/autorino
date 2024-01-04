import gnss

def main():

    begin = "2022-01-01"
    end = "2022-01-31"

    # Creation d'une station SNEG avec un recepteur GB-1000
    sneg_receiver = gnss.GB_1000_Receiver("sneg.ovpf.ipgp.fr", "ftp", 8002)
    sneg = gnss.Station("SNEG")
    sneg.add_receiver(sneg_receiver)

    # Creation d'une station BOMG avec un recepteur GB-1000 et un PolaRx5
    bomg_receiver1 = gnss.GB_1000_Receiver("bomg1.ovpf.ipgp.fr", "ftp", 8002)
    bomg_receiver2 = gnss.Polarx5_Receiver("bomg2.ovpf.ipgp.fr", "ftp", 22, "admin")
    bomg = gnss.Station("BOMG", (bomg_receiver1, bomg_receiver2))

    # Creation du network PF avec les stations SNEG et BOMG
    network = gnss.Network("PF", (sneg, bomg))

    # Telechargement des donnees pour chaque stations/recepteurs du reseau PF
    for station in network.get_stations():
        print("Processing station %s" % (station.get_name()))
        for receiver in station.get_receivers():
            print("  Processing receiver %s" % (receiver.get_hostname()))
            print("  Fichiers sur le recepteur : %s " % (receiver.get_file_list()))
            receiver.download_period(begin,end)

if __name__ == "__main__":
    main()
