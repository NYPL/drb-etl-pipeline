from mappings.doab import map_doab_record
from model import Source
from lxml import etree

OAI_NAMESPACES = {
    'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'datacite': 'https://schema.datacite.org/meta/kernel-4.1/metadata.xsd',
    'oapen': 'http://purl.org/dc/elements/1.1/',
    'oaire': 'https://raw.githubusercontent.com/rcic/openaire4/master/schemas/4.0/oaire.xsd'
}

def test_map_doab_record():
    with open('tests/fixtures/test-doab.xml') as f:
        oaidc_records = etree.parse(f)

    for record in oaidc_records.xpath('//oai_dc:dc', namespaces=OAI_NAMESPACES):
        if record is None:
            continue

        parsed_record = map_doab_record(doab_record=record, namespaces=OAI_NAMESPACES)
        assert parsed_record.source == Source.DOAB.value