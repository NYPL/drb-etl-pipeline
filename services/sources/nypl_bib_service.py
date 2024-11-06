from datetime import datetime, timedelta, timezone
import os
import requests
from typing import Optional

from logger import createLog
from managers.db import DBManager
from managers.nyplApi import NyplApiManager
from mappings.nypl import NYPLMapping
from .source_service import SourceService
from sqlalchemy import text


logger = createLog(__name__)


class NYPLBibService(SourceService):
    def __init__(self):
        self.bib_db_connection = DBManager(
            user=os.environ['NYPL_BIB_USER'],
            pswd=os.environ['NYPL_BIB_PSWD'],
            host=os.environ['NYPL_BIB_HOST'],
            port=os.environ['NYPL_BIB_PORT'],
            db=os.environ['NYPL_BIB_NAME']
        )
        self.bib_db_connection.generateEngine()

        self.nypl_api_manager = NyplApiManager()
        self.nypl_api_manager.generateAccessToken()

        self.location_codes = self.load_location_codes()
        self.cce_api = os.environ['BARDO_CCE_API']

    def get_records(
        self,
        full_import: bool=False,
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[NYPLMapping]:
        records = []
        nypl_bib_query = 'SELECT id, nypl_source, publish_year, var_fields FROM bib'

        if not full_import:
            nypl_bib_query += ' WHERE updated_date > '
            
            if start_timestamp:
                nypl_bib_query += "'{}'".format(start_timestamp)
            else:
                startDateTime = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
                nypl_bib_query += "'{}'".format(startDateTime.strftime('%Y-%m-%dT%H:%M:%S%z'))

        if offset:
            nypl_bib_query += ' OFFSET {}'.format(offset)

        if limit:
            nypl_bib_query += ' LIMIT {}'.format(limit)

        with self.bib_db_connection.engine.connect() as db_connection:
            bib_results = db_connection.execution_options(stream_results=True).execute(text(nypl_bib_query))
            
            for bib in bib_results:
                bib = self._map_bib(bib)
                
                if bib['var_fields'] is None:
                    continue

                nypl_bib_record = self.parse_nypl_bib(bib)
                records.append(nypl_bib_record)

        return records

    def parse_nypl_bib(self, bib) -> NYPLMapping:
        try:
            if self.is_pd_research_bib(dict(bib)):
                bib_items = self.fetch_bib_items(dict(bib))
                
                nypl_record = NYPLMapping(bib, bib_items, self.statics, self.location_codes)
                nypl_record.applyMapping()
                
                return nypl_record
        except Exception:
            logger.exception('Failed to parse NYPL bib {}'.format(bib.get('id')))

    def fetch_bib_items(self, bib):
        bib_endpoint = 'bibs/{}/{}/items'.format(bib['nypl_source'], bib['id'])

        return self.nypl_api_manager.queryApi(bib_endpoint).get('data', [])

    def _map_bib(self, bib): 
        try:
            id, nypl_source, publish_year, var_fields = bib
            
            return {
                'id': id,
                'nypl_source': nypl_source,
                'publish_year': publish_year,
                'var_fields': var_fields
            }
        except:
            return bib

    def load_location_codes(self):
        return requests.get(os.environ['NYPL_LOCATIONS_BY_CODE']).json()

    def is_pd_research_bib(self, bib):
        current_year = datetime.today().year

        try:
            pub_year = int(bib['publish_year'])
        except Exception:
            pub_year = current_year

        if pub_year > 1965:
            return False
        elif pub_year > current_year - 95:
            copyright_status = self.get_copyright_status(bib['var_fields'])
            
            if not copyright_status: 
                return False

        bib_status = self.nypl_api_manager.queryApi('bibs/{}/{}/is-research'.format(bib['nypl_source'], bib['id']))

        return bib_status.get('isResearch', False) is True

    def get_copyright_status(self, var_fields):
        lccn_data = list(filter(lambda field: field.get('marcTag', None) == '010', var_fields))

        if not len(lccn_data) == 1:
            return False

        lccn_no = lccn_data[0]['subfields'][0]['content'].replace('sn', '').strip()

        copyright_url = f'{self.cce_api}/lccn/{lccn_no}'

        copyright_response = requests.get(copyright_url)
        
        if copyright_response.status_code != 200:
            return False

        copyright_data = copyright_response.json()

        if len(copyright_data['data']['results']) > 0:
            return False if len(copyright_data['data']['results'][0]['renewals']) > 0 else True

        return False   
