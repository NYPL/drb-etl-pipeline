from managers import DBManager
from model import Record

from logger import create_log


logger = create_log(__name__)


class CoreProcess(DBManager):
    def __init__(self, process, customFile, ingestPeriod, singleRecord):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod
        self.singleRecord = singleRecord
