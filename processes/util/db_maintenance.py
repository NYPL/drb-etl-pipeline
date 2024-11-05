from sqlalchemy import text

from logger import create_logger
from managers import DBManager

logger = create_logger(__name__)


class DatabaseMaintenanceProcess():
    VACUUMING_TABLES = ['records', 'items', 'editions', 'works', 'links', 'rights', 'identifiers']

    def __init__(self, *args):
        self.db_manager = DBManager()

    def runProcess(self):
        try:
            self.db_manager.generateEngine()
            self.db_manager.createSession()

            self.vacuum_tables()

            logger.info('Database maintenance complete')
        except Exception as e:
            logger.exception('Failed to run database maintenance')
            raise e
        finally:
            self.db_manager.closeConnection()

    def vacuum_tables(self):
        logger.info(f'Vacuuming tables: {self.VACUUMING_TABLES}')

        with (
            self.db_manager.engine.connect() as db_connnection,
            db_connnection.execution_options(isolation_level='AUTOCOMMIT')
        ):         
            for table_name in self.VACUUMING_TABLES:
                logger.info(f'Vacuuming {table_name} table')
                db_connnection.execute(text(f'VACUUM ANALYZE {table_name};'))
