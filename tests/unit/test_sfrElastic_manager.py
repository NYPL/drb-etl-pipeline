import pytest

from managers import SFRElasticRecordManager


class TestSFRElasticRecordManager:
    @pytest.fixture
    def testInstance(self, mocker):
        return SFRElasticRecordManager(mocker.MagicMock())

    def test_initializer(self, testInstance, mocker):
        assert isinstance(testInstance.dbWork, mocker.MagicMock)
        assert testInstance.work == None

    def test_getCreateWork_new(self, testInstance, mocker):
        mockEnhance = mocker.patch.object(SFRElasticRecordManager, 'enhanceWork')
        mockESWork = mocker.patch('managers.sfrElasticRecord.ESWork')
        mockESWork.get.return_value = None
        mockESWork.return_value = 'testESWork'

        testInstance.getCreateWork()

        assert testInstance.work == 'testESWork'
        mockESWork.get.assert_called_once
        mockESWork.assert_called_once
        mockEnhance.assert_called_once

    def test_getCreateWork_existing(self, testInstance, mocker):
        mockEnhance = mocker.patch.object(SFRElasticRecordManager, 'enhanceWork')
        mockUpdate = mocker.patch.object(SFRElasticRecordManager, 'updateWork')
        mockESRec = mocker.MagicMock()
        mockESWork = mocker.patch('managers.sfrElasticRecord.ESWork')
        mockESWork.get.return_value = mockESRec

        testInstance.getCreateWork()

        assert testInstance.work == mockESRec
        mockESWork.get.assert_called_once
        mockESWork.assert_not_called
        mockUpdate.assert_called_once_with({})
        mockEnhance.assert_called_once

    def test_saveWork(self, testInstance, mocker):
        testInstance.work = mocker.MagicMock()

        testInstance.saveWork()

        testInstance.work.save.assert_called_once

    def test_updateWork(self, testInstance, mocker):
        testInstance.work = mocker.MagicMock()

        testInstance.updateWork({'title': 'Test Title', 'id': 1})

        assert testInstance.work.title == 'Test Title'
        assert testInstance.work.id == 1



