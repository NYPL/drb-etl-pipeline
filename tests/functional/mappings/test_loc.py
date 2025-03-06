import json
from mappings.loc import LOCMapping
from model import Source


def test_map_loc_record():
    with open('tests/fixtures/test-loc.json') as f:
        loc_data = json.load(f)

    loc_mapping = LOCMapping(loc_data)
    loc_mapping.applyMapping()

    assert loc_mapping.record.title == 'Guia de espécies fitoterápicas brasileiras'
    assert loc_mapping.record.source_id == '2024350289|lccn'
    assert loc_mapping.record.identifiers == ['2024350289|lccn', 'RS175.B7|call_number']
    assert loc_mapping.record.authors == ['capote, anna claudia morais de oliveira|||true', 'beltrame, flávio luís|||true']
    assert loc_mapping.record.medium == 'book'
    assert loc_mapping.record.contributors == ['capote, anna claudia morais de oliveira|||contributor', 'beltrame, flávio luís|||contributor']
    assert loc_mapping.record.languages == ['||por']
    assert loc_mapping.record.extent == '1 online resource (225 pages) : illustrations (chiefly color)'
    assert loc_mapping.record.spatial == 'Brazil'
    assert loc_mapping.record.abstract == 'Includes bibliographical references. Description based on online resource; title from PDF title page (Atena Editora, viewed February 26, 2025).'
    assert loc_mapping.record.publisher == ['Atena Editora', 'AL Editora Olyver']
    assert loc_mapping.record.dates == ['2024|publication_date']
    assert loc_mapping.record.subjects == ['Materia medica, Vegetable--Brazil||', 'Medicinal plants--Brazil--Identification||']
    assert loc_mapping.record.rights == 'loc|Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International CC BY-NC-ND 4.0 https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode|||'
    assert loc_mapping.record.is_part_of == ['open access books|collection', 'general collections|collection', 'catalog|collection', 'lc online resource|collection']
    assert loc_mapping.record.has_part == ['1|https://tile.loc.gov/storage-services/master/gdc/gdcebookspublic/20/24/35/02/89/2024350289/2024350289.pdf|loc|application/pdf|{"catalog": false, "reader": false, "embed": false, "download": true, "cover": false}']
