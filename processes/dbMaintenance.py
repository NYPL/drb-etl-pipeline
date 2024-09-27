from .core import CoreProcess
from logging import logger


class DatabaseMaintenanceProcess(CoreProcess):
    VACUUMING_TABLES = [
        'records', 'items', 'editions', 'works', 'links', 'rights',
        'identifiers'
    ]

    def __init__(self, *args):
        super(DatabaseMaintenanceProcess, self).__init__(*args[:4])

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

    def runProcess(self):
        self.vacuumTables()

        self.closeConnection()

    def vacuumTables(self):
        logger.info('Starting Vacuum of in-use tables')
        with self.engine.connect() as conn:
            with conn.execution_options(isolation_level='AUTOCOMMIT'):
                for table in self.VACUUMING_TABLES:
                    self.vacuumTable(conn, table)

    @staticmethod
    def vacuumTable(conn, table):
        logger.info(f'Vacuuming {table}')
        vacuumStr = f'VACUUM ANALYZE {table};'
        conn.execute(vacuumStr)
