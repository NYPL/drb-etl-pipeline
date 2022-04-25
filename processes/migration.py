from alembic import config
from .core import CoreProcess
from logger import createLog

logger = createLog(__name__)


class MigrationProcess(CoreProcess):
    def __init__(self, *args):
        super(MigrationProcess, self).__init__(*args[:4])

        self.options = args[6]

    def runProcess(self):
        logger.info('Running database migration')

        alembicArgs = ['--raiseerr'] + self.options

        config.main(argv=alembicArgs)
