from client import ArkClient
from pathlib import Path


class Client:
    def __init__(self):
        self.home = str(Path.home())
        #net = n.split('_')
        #coin, network = net[0], net[1]
    
        #self.core = self.home+'/.config/'+coin+'-core/'+network
        #self.tbw = self.home+'/core2_tbw'
        
        
    def get_client(self, api_port, ip="localhost"):
        return ArkClient('http://{0}:{1}/api'.format(ip, api_port))
