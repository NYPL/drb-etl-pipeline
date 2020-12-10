from .core import CoreProcess
from api.app import FlaskAPI


class APIProcess(CoreProcess):
    def __init__(self, process, customFile, ingestPeriod):
        super(APIProcess, self).__init__(process, customFile, ingestPeriod)

        self.createElasticConnection()
        self.generateEngine()
        self.api = FlaskAPI(self.client, self.engine)

    def runProcess(self):
        self.api.run()
