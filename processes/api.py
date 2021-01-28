from .core import CoreProcess
from api.app import FlaskAPI


class APIProcess(CoreProcess):
    def __init__(self, *args):
        super(APIProcess, self).__init__(*args[:4])

        self.createElasticConnection()
        self.generateEngine()
        self.api = FlaskAPI(self.client, self.engine)

    def runProcess(self):
        self.api.run()
