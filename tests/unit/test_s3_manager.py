from managers.oclcClassify import ClassifyManager
from botocore.exceptions import ClientError
import hashlib
import pytest

from managers.s3 import S3Manager, S3Error


class TestS3Manager:
    @pytest.fixture
    def testInstance(self, mocker):
        testInstance = S3Manager()
        testInstance.s3Client = mocker.MagicMock()

        return testInstance

    def test_initializer(self):
        assert isinstance(S3Manager(), S3Manager)

    def test_createS3Client(self, testInstance, mocker):
        mockBoto = mocker.patch('managers.s3.boto3')
        mockBoto.client.return_value = 'testClient'
        mocker.patch.dict('os.environ', {'AWS_ACCESS': 'access', 'AWS_SECRET': 'secret', 'AWS_REGION': 'region'})
        testInstance.createS3Client()

        assert testInstance.s3Client == 'testClient'
        mockBoto.client.assert_called_once_with(
            's3', aws_access_key_id='access', aws_secret_access_key='secret', region_name='region'
        )

    def test_createS3Bucket_success(self, testInstance):
        testInstance.s3Client.create_bucket.return_value = {'Location': 'testing'}

        assert testInstance.createS3Bucket('testBucket', 'test-perms') is True
        testInstance.s3Client.create_bucket.assert_called_once_with(
            ACL='test-perms', Bucket='testBucket'
        )

    def test_createS3Bucket_failure(self, testInstance):
        testInstance.s3Client.create_bucket.return_value = {}

        with pytest.raises(S3Error):
            testInstance.createS3Bucket('testBucket', 'test-perms')

    def test_putObjectInBucket_success(self, testInstance, mocker):
        mockHash = mocker.patch.object(S3Manager, 'getmd5HashOfObject')
        mockHash.return_value = 'testMd5Hash'
        mockGet = mocker.patch.object(S3Manager, 'getObjectFromBucket')
        mockGet.return_value = None

        testInstance.s3Client.put_object.return_value = 'testObjectResponse'

        testResponse = testInstance.putObjectInBucket('testObj', 'testKey', 'testBucket')

        assert testResponse == 'testObjectResponse'

        mockHash.assert_called_once_with('testObj')
        mockGet.assert_called_once_with('testKey', 'testBucket', md5Hash='testMd5Hash')
        testInstance.s3Client.put_object.assert_called_once_with(
            ACL='public-read', Body='testObj', Bucket='testBucket', Key='testKey'
        )

    def test_putObjectInBucket_existing_outdated(self, testInstance, mocker):
        mockHash = mocker.patch.object(S3Manager, 'getmd5HashOfObject')
        mockHash.return_value = 'testMd5Hash'
        mockExisting = mocker.MagicMock()
        mockExisting.statusCode = 301
        mockGet = mocker.patch.object(S3Manager, 'getObjectFromBucket')
        mockGet.return_value = mockExisting

        testInstance.s3Client.put_object.return_value = 'testObjectResponse'

        testResponse = testInstance.putObjectInBucket('testObj', 'testKey', 'testBucket')

        assert testResponse == 'testObjectResponse'

        mockHash.assert_called_once_with('testObj')
        mockGet.assert_called_once_with('testKey', 'testBucket', md5Hash='testMd5Hash')
        testInstance.s3Client.put_object.assert_called_once_with(
            ACL='public-read', Body='testObj', Bucket='testBucket', Key='testKey'
        )

    def test_putObjectInBucket_existing_unmodified(self, testInstance, mocker):
        mockHash = mocker.patch.object(S3Manager, 'getmd5HashOfObject')
        mockHash.return_value = 'testMd5Hash'
        mockGet = mocker.patch.object(S3Manager, 'getObjectFromBucket')
        mockGet.return_value = {'ResponseMetadata': {'HTTPStatusCode': 304}}

        testResponse = testInstance.putObjectInBucket('testObj', 'testKey', 'testBucket')

        assert testResponse == None

        mockHash.assert_called_once_with('testObj')
        mockGet.assert_called_once_with('testKey', 'testBucket', md5Hash='testMd5Hash')
        testInstance.s3Client.put_object.assert_not_called

    def test_putObjectInBucket_error(self, testInstance, mocker):
        mockHash = mocker.patch.object(S3Manager, 'getmd5HashOfObject')
        mockHash.return_value = 'testMd5Hash'
        mockGet = mocker.patch.object(S3Manager, 'getObjectFromBucket')
        mockGet.return_value = None

        testInstance.s3Client.put_object.side_effect = ClientError({}, 'Testing')

        with pytest.raises(S3Error):
            testInstance.putObjectInBucket('testObj', 'testKey', 'testBucket')

    def test_getObjectFromBucket_success(self, testInstance, mocker):
        testInstance.s3Client.get_object.return_value = 'testObject'

        testResponse = testInstance.getObjectFromBucket('testKey', 'testBucket')

        assert testResponse == 'testObject'
        testInstance.s3Client.get_object.assert_called_once_with(
            Bucket='testBucket', Key='testKey', IfNoneMatch=None
        )

    def test_getObjectFromBucket_error(self, testInstance, mocker):
        testInstance.s3Client.get_object.side_effect = ClientError({}, 'Testing')


        with pytest.raises(S3Error):
            testResponse = testInstance.getObjectFromBucket('testKey', 'testBucket')

    def test_getmd5HashOfObject(self):
        S3Manager.getmd5HashOfObject('testing'.encode('utf-8')) == 'ae2b1fca515949e5d54fb22b8ed95575'
