from glob import glob
import json
import re


class StaticManager:
    def __init__(self):
        super(StaticManager, self).__init__()
        self.statics = {}
        self.loadStaticFiles()

    def loadStaticFiles(self):
        for staticPath in glob('./static/*.json'):
            self.parseStaticPath(staticPath)
    
    def parseStaticPath(self, staticPath):
        staticName = re.search(r'\/([a-z0-9]+)\.json', staticPath).group(1)

        with open(staticPath, 'r') as staticFile:
            staticJSON = json.load(staticFile)
            self.setStaticValues(staticJSON, staticName)
    
    def setStaticValues(self, staticJSON, staticName):
        staticValDict = {}

        for key, value in staticJSON.items():
            staticValDict[key] = value
        
        self.statics[staticName] = staticValDict
