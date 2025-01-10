from bs4 import BeautifulSoup
import pytest
import requests
import pprint
from requests.exceptions import ReadTimeout
from services import PublisherBacklistService
from tests.helper import TestHelpers
from unittest.mock import Mock

class TestBacklistService:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testService(self, mocker):
        class TestBacklistService(PublisherBacklistService):
            def __init__(self):
                self.s3_manager = mocker.MagicMock()
                self.drive_service = mocker.MagicMock()
                self.drive_service.get_file_metadata.side_effect = [{'name': 'full_access.pdf'}, {'name': 'limited_access.pdf'}]
                self.ssm_service = mocker.MagicMock()
                self.file_bucket = 'regular-bucket'
                self.limited_file_bucket = 'limited-bucket'
                self.title_prefix = 'titles/publisher_backlist'
        return TestBacklistService()
                
    @pytest.fixture
    def test_airtable_records(self):
        return [
        {
        "id": "recPTBrKmZnsguK8M",
        "createdTime": "2023-12-21T19:06:11.000Z",
        "fields": {
            "Author(s)": "Aristophanes",
            "Title": "The Birds. Translated by William Arrowsmith, with sketches by Stuart Ross",
            "Pub Date": "1961",
            "Rights status linked record": ["recX5aollpn3ubbkM", "recLXN9DU6RJehpDB"],
            "Project steps": ["recUI0frKtIAtVZND"],
            "File ID 1": "39015002278961",
            "Digitial copy at press?": "yes",
            "Digital copy received": True,
            "Project": ["recDhurlgY5mQ4F8p"],
            "OCLC": "603198",
            "Contributors": "Translated by William Arrowsmith, with sketches by Stuart Ross",
            "Rights classification by publisher (UMP only)": "D-C",
            "Rights review / PD or renewal": True,
            "Hathi rights code": "ic",
            "DRB Rights Classification": "public domain",
            "Digitization status": ["recjlYWETJ1aOiWTG"],
            "DRB_File Location": "https://drive.google.com/open?id=1Cy1LF_G8OyRHp0UpsV2zDv4gNiXIIh7T",
            "DRB_Ready to ingest": True,
            "Access types": ["recVXZOA70wwC1ciY"],
            "Next step (from Project steps)": ["Ready to ingest"],
            "Rights status (from Rights status linked record)": [
                "public domain",
                "cleared by rights team",
            ],
            "Publisher (from Project)": ["University of Michigan Press"],
            "Project status": ["In process"],
            "Status (from Digitization status)": ["Publisher digitized"],
            "Last Modified": "2024-06-20T17:15:35.000Z",
            "DRB_Record ID": "recPTBrKmZnsguK8M",
            "Project Name (from Project)": ["Test Backlist"],
            "Access type in DRB (from Access types)": ["Full access"],
        },
    },
    {
        "id": "recRvPlHdLkM0KIem",
        "createdTime": "2023-12-21T19:06:11.000Z",
        "fields": {
            "Author(s)": "Broadbooks, Harold E.",
            "Title": "Life history and ecology of the chipmunk, Eutamias amoenus, in eastern Washington",
            "Pub Date": "1958",
            "Copyright holder": "Publisher",
            "Rights status linked record": ["recX5aollpn3ubbkM", "recLXN9DU6RJehpDB"],
            "Project steps": ["recUI0frKtIAtVZND"],
            "File ID 1": "39015032124508",
            "Digitial copy at press?": "yes",
            "Digital copy received": True,
            "Project": ["recDhurlgY5mQ4F8p"],
            "OCLC": "1892309",
            "Rights classification by publisher (UMP only)": "A",
            "Rights review / PD or renewal": True,
            "Hathi rights code": "und",
            "DRB Rights Classification": "public domain",
            "Digitization status": ["recjlYWETJ1aOiWTG"],
            "DRB_File Location": "https://drive.google.com/open?id=19ibZ2CtAzIflL4N1tf3NoBonr2-rxfQA",
            "DRB_Ready to ingest": True,
            "Access types": ["recVarWgjQaYXJZDM"],
            "Next step (from Project steps)": ["Ready to ingest"],
            "Rights status (from Rights status linked record)": [
                "public domain",
                "cleared by rights team",
            ],
            "Publisher (from Project)": ["University of Michigan Press"],
            "Project status": ["In process"],
            "Status (from Digitization status)": ["Publisher digitized"],
            "Last Modified": "2024-06-20T17:15:35.000Z",
            "DRB_Record ID": "recRvPlHdLkM0KIem",
            "Project Name (from Project)": ["Test Backlist"],
            "Access type in DRB (from Access types)": [
                "Limited access/login for read & download"
            ],
        },
    }]
                
    def test_get_records(self, test_airtable_records, testService, mocker):
        mock_records = mocker.patch('services.PublisherBacklistService.get_publisher_backlist_records', return_value=test_airtable_records)
        mock_get = mocker.patch.object(testService.s3_manager, 'putObjectInBucket')
        mock_get.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        test_get_records = testService.get_records()
        assert len(test_get_records) == 2
        mapped_full_access_record = test_get_records[0].record
        full_access_manifest_link = mapped_full_access_record.has_part[0].split('|')
        assert full_access_manifest_link[1] == 'https://regular-bucket.s3.amazonaws.com/manifests/publisher_backlist/Test Backlist/recPTBrKmZnsguK8M.json'
        assert full_access_manifest_link[2] == 'Test Backlist'
        assert full_access_manifest_link[3] == 'application/webpub+json'
        assert full_access_manifest_link[4] == '{"catalog": false, "download": false, "reader": true, "embed": false}'
        full_access_title_link = mapped_full_access_record.has_part[1].split('|')
        assert full_access_title_link[1] == 'https://regular-bucket.s3.amazonaws.com/titles/publisher_backlist/Test Backlist/full_access.pdf'
        assert full_access_title_link[2] == 'Test Backlist'
        assert full_access_title_link[3] == 'application/pdf'
        assert full_access_title_link[4] == '{"catalog": false, "download": true, "reader": false, "embed": false, "nypl_login": false}'
        mapped_limited_access_record = test_get_records[1].record
        limited_access_manifest_link = mapped_limited_access_record.has_part[0].split('|')
        assert limited_access_manifest_link[1] == 'https://regular-bucket.s3.amazonaws.com/manifests/publisher_backlist/Test Backlist/recRvPlHdLkM0KIem.json'
        assert limited_access_manifest_link[2] == 'Test Backlist'
        assert limited_access_manifest_link[3] == 'application/webpub+json'
        assert limited_access_manifest_link[4] == '{"catalog": false, "download": false, "reader": true, "embed": false, "fulfill_limited_access": false}'
        limited_access_title_link = mapped_limited_access_record.has_part[1].split('|')
        assert limited_access_title_link[1] == 'https://limited-bucket.s3.amazonaws.com/titles/publisher_backlist/Test Backlist/limited_access.pdf'
        assert limited_access_title_link[2] == 'Test Backlist'
        assert limited_access_title_link[3] == 'application/pdf'
        assert limited_access_title_link[4] == '{"catalog": false, "download": true, "reader": false, "embed": false, "nypl_login": false}'