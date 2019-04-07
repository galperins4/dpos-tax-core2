import os
from dotenv import load_dotenv
from pathlib import Path
from client import ArkClient

class Network():
    def __init__(self, network):
        self.home = str(Path.home())
        self.network = network
        env_path = self.home + '/dpos-tax-core2/network/' + self.network
        load_dotenv(env_path)
        self.load_network()
        self.client = self.get_client()
        
        
    def load_network(self):
         self.epoch = os.getenv("EPOCH").split(',')
         self.version = os.getenv("VERSION")
         self.wif = os.getenv("WIF")
         self.api_port = os.getenv("API_PORT")
         self.database = os.getenv("DATABASE")
         self.database_user = os.getenv("DATABASE_USER")
         self.database_password = os.getenv("DATABASE_PASSWORD")

    def get_client(self, ip="localhost"):
         port = self.api_port
         return ArkClient('http://{0}:{1}/api'.format(ip, port))
