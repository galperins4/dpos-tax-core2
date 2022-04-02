from client import ArkClient
from pathlib import Path


class Client:
    def __init__(self):
        self.home = str(Path.home())
        
        
    def get_client(self, api_port, ip="localhost"):
        return ArkClient('http://{0}:{1}/api'.format(ip, api_port))
