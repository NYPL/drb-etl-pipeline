
class CoreProcess():
    def __init__(self, process, customFile, ingestPeriod, singleRecord):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod
        self.singleRecord = singleRecord
