from abc import ABC, abstractmethod

class Network:
    '''
    Classe representant un reseau GNSS
    '''

    '''
    Le constructeur
    '''
    def __init__(self, name, stations=[]):
        self.name = name
        self.stations = stations

    '''
    Les "geters" et "seters"
    '''
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_stations(self):
        return self.stations

    '''
    Ajoute une station
    '''
    def add_station(self, station):
        self.stations.append(station)

    '''
    Ajoute une liste de stations
    '''
    def add_stations(self, stations):
        self.stations = self.stations + stations


class Station:
    '''
    Classe representant une station GNSS
    '''

    '''
    Le constructeur
    '''
    def __init__(self, name, receivers=[]):
        self.name = name
        self.receivers = receivers

    '''
    Les "geters" et "seters"
    '''
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_receivers(self):
        return self.receivers

    '''
    Ajoute un recepteur
    '''
    def add_receiver(self, receiver):
        self.receivers.append(receiver)

    '''
    Ajoute une liste de recepteur
    '''
    def add_receivers(self, receivers):
        self.receivers = self.receivers + receivers

class Receiver(ABC):
    '''
    Classe abstraite representant les recepteurs GNSS
    '''

    '''
    Le constructeur
    '''
    def __init__(self, hostname, protocol, port, user, password):
        self.hostname = hostname
        self.protocol = protocol
        self.user = user
        self.password = password
        self.port = port

    '''
    Les geters et les seters
    Herites par les classes filles
    '''
    def get_hostname(self):
        return self.hostname

    def set_hostname(self, hostname):
        self.hostname = hostname


    '''
    Methode abstraite
    A definir dans la classe fille
    '''
    @abstractmethod
    def get_file_list(self):
        pass

    '''
    Methode abstraite
    A definir dans la classe fille
    '''
    @abstractmethod
    def download_file(self, file):
        pass

    '''
    Methode abstraite
    A definir dans la classe fille
    '''
    @abstractmethod
    def download_period(self, begin, end):
        pass

class Receiver_Topcon(Receiver):
    '''
    Classe representant les recepteurs GNSS Topcon GB-1000
    '''

    '''
    Le constructeur
    Il appelle le constructeur de la classe mere
    '''
    def __init__(self, hostname, protocol, port):
        super().__init__(hostname, protocol, port)

    '''
    Implementation de la classe abstraite
    '''
    def get_file_list(self):
        return "Une liste de fichier de Topncon GB-1000"

    '''
    Implementation de la classe abstraite
    '''
    def download_file(self, file):
        print("Downloading file %s" % (file))
        return 0

    '''
    Implementation de la classe abstraite
    '''
    def download_period(self, begin, end):
        print("Downloading files from %s to %s" % (begin, end))
        for i in range(0, 5):
            self.download_file("file" + str(i))

class Receiver_Septentrio(Receiver):
    '''
    Classe representant les recepteurs GNSS Septentrio PolaRx5
    '''

    '''
    Le constructeur
    Il appelle le constructeur de la classe mere
    Il initialise un attribut supplementaire
    '''
    def __init__(self, hostname, protocol, port, login):
        super().__init__(hostname, protocol, port)
        self.login = login

    '''
    Implementation de la classe abstraite
    '''
    def get_file_list(self):
        return "Une liste de fichier de Septentrio PolaRx5"

    '''
    Implementation de la classe abstraite
    '''
    def download_file(self, file):
        print("Downloading file %s" % (file))
        return 0

    '''
    Implementation de la classe abstraite
    '''
    def download_period(self, begin, end):
        print("Downloading files from %s to %s" % (begin, end))
        for i in range(20, 26):
            self.download_file("file" + str(i))

    '''
    Les "geters" et "seters"
    '''
    def set_login(self, login):
        self.login = login

    def get_login(self):
        return self.login
