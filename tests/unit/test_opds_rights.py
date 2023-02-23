import pytest

from api.opds2.rights import Rights, OPDS2RightsException


class TestRights:
    def test_initializer(self):
        testRights = Rights(license='test1', rightsStatement='test2', source='test3')

        assert testRights.attrs == set(['license', 'rightsStatement', 'source'])
        assert testRights.license == 'test1'
        assert testRights.rightsStatement == 'test2'
        assert testRights.source == 'test3'

    def test_addField(self):
        testRights = Rights()

        testRights.addField('license', 'test1')

        assert testRights.attrs == set(['license'])
        assert testRights.license == 'test1'

    def test_addFields_dict(self, mocker):
        testRights = Rights()

        mockAdd = mocker.patch.object(Rights, 'addField')

        testRights.addFields({'license': 'test1', 'rightsStatement': 'test2', 'source': 'test3'})

        mockAdd.assert_has_calls([
            mocker.call('license', 'test1'), mocker.call('rightsStatement', 'test2'), mocker.call('source', 'test3')
        ])

    def test_addFields_list(self, mocker):
        testRights = Rights()

        mockAdd = mocker.patch.object(Rights, 'addField')

        testRights.addFields([('license', 'test1'), ('rightsStatement', 'test2'), ('source', 'test3')])

        mockAdd.assert_has_calls([
            mocker.call('license', 'test1'), mocker.call('rightsStatement', 'test2'), mocker.call('source', 'test3')
        ])

    def test_iter_success(self):
        testRights = Rights(license='test1', rightsStatement='test2', source='test3')

        assert dict(testRights) == {'license': 'test1', 'rightsStatement': 'test2', 'source': 'test3'}

    def test_iter_error_missing_field(self):
        testRights = Rights(license='test1')

        with pytest.raises(OPDS2RightsException):
            dict(testRights)

    def test_iter_error_unpermitted_field(self):
        testRights = Rights(other='testing')

        with pytest.raises(OPDS2RightsException):
            dict(testRights)

    def test_repr(self):
        testRights = Rights(license='test1', rightsStatement='test2', source='test3')

        assert str(testRights) == '<Rights(license=test1, rightsStatement=test2, source=test3)>'

