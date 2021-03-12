import pandas as pd
import pytest


from managers.kMeans import KMeansManager, TextSelector, NumberSelector


class TestKMeansModel(object):
    @pytest.fixture
    def testModel(self, testInstances, testClusters):
        testModel = KMeansManager([])
        testModel.instances = testInstances
        testModel.clusters = testClusters
        testModel.currentK = 1
        return testModel
    
    @pytest.fixture
    def testInstances(self, mocker):
        return [
            TestKMeansModel.createInstance(
                mocker,
                spatial='test',
                dates=['date1', 'date2'],
                publisher=['agent1', 'agent2'],
                edition=['edition1'],
                uuid=1
            ),
            TestKMeansModel.createInstance(
                mocker,
                spatial=False,
                dates=None,
                publisher=None,
                edition=['edition1'],
                uuid=2
            ),
            TestKMeansModel.createInstance(
                mocker,
                spatial='test',
                dates=['date1'],
                publisher=['agent2', 'agent3'],
                edition=['edition1'],
                uuid=3
            )
        ]
    
    @pytest.fixture
    def testClusters(self):
        return {
            0: [
                pd.DataFrame({
                    'pubDate': 1900,
                    'publisher': 'test',
                    'place': 'testtown',
                    'uuid': 1,
                    'edition': '',
                    'volume': '',
                    'extent': '',
                    'table_of_contents': '',
                    'summary': ''
                }, index=[0]),
                pd.DataFrame({
                    'pubDate': 1900,
                    'publisher': 'test',
                    'place': 'testtown',
                    'uuid': 2,
                    'edition': '',
                    'volume': '',
                    'extent': '',
                    'table_of_contents': '',
                    'summary': ''
                }, index=[0])
            ],
            1: [
                pd.DataFrame({
                    'pubDate': 2000,
                    'publisher': 'test',
                    'place': 'testtown',
                    'uuid': 3,
                    'edition': '',
                    'volume': '',
                    'extent': '',
                    'table_of_contents': '',
                    'summary': ''
                }, index=[0]),
                pd.DataFrame({
                    'pubDate': 1950,
                    'publisher': 'test',
                    'place': 'testtown',
                    'uuid': 4,
                    'edition': '',
                    'volume': '',
                    'extent': '',
                    'table_of_contents': '',
                    'summary': ''
                }, index=[0])
            ]
        }

    @staticmethod
    def createInstance(mocker, **kwargs):
        mockInst = mocker.MagicMock()
        for key, value in kwargs.items():
            setattr(mockInst, key, value)
        return mockInst
    
    def test_kModel_init(self, testModel):
        assert len(testModel.instances) == 3
        assert testModel.df == None
        assert isinstance(testModel.clusters, dict)

    def test_createPipeline(self, testModel, mocker):
        mockPipeline = mocker.patch('managers.kMeans.Pipeline')
        mockPipeline.side_effect = ['placePipe', 'pubPipe', 'edPipe', 'datePipe', 'mainPipe']
        mockFeatureUnion = mocker.patch('managers.kMeans.FeatureUnion')
        mockFeatureUnion.return_value = 'testUnion'
        mockKMeans = mocker.patch('managers.kMeans.KMeans')
        mockKMeans.return_value = 'testKMeans'

        testPipeline = testModel.createPipeline(['place', 'publisher'])

        assert testPipeline == 'mainPipe'
        mockFeatureUnion.assert_called_once_with(
            transformer_list=[('place', 'placePipe'), ('publisher', 'pubPipe')],
            transformer_weights={'place': 0.5, 'publisher': 1.0}
        )
        mockKMeans.assert_called_once_with(n_clusters=1, max_iter=150, n_init=5)
        assert mockPipeline.call_args == mocker.call([('union', 'testUnion'), ('kmeans', 'testKMeans')])
    
    def test_pubProcessor_str(self):
        cleanStr = KMeansManager.pubProcessor('Testing & Testing,')
        assert cleanStr == 'testing and testing'

        cleanStr2 = KMeansManager.pubProcessor('[publisher not identified]')
        assert cleanStr2 == ''
    
    def test_pubProcessor_list(self):
        cleanStr = KMeansManager.pubProcessor(['hello', 'sn', 'goodbye'])
        assert cleanStr == 'hello goodbye'
    
    def test_pubProcessor_none(self):
        cleanStr = KMeansManager.pubProcessor(None)
        assert cleanStr == ''
    
    def test_createDF(self, mocker, testModel):
        mockGetPub = mocker.patch.object(KMeansManager, 'getPublisher')
        mockGetPub.side_effect = ['agent1', False, False]
        mockGetDate = mocker.patch.object(KMeansManager, 'getPubDateFloat')
        mockGetDate.side_effect = [1900, False, 1901]
        mockGetDate = mocker.patch.object(KMeansManager, 'getEditionStatement')
        mockGetDate.side_effect = ['ed1', 'ed2', False]

        testModel.createDF()
        assert isinstance(testModel.df, pd.DataFrame)
        assert testModel.df.iloc[0]['uuid'] == 1
        assert testModel.df.iloc[1]['uuid'] == 3
        assert testModel.maxK == 2

    def test_createDF_maxK_1000_plus(self, mocker, testModel):
        mockGetPub = mocker.patch.object(KMeansManager, 'getPublisher')
        mockGetPub.side_effect = ['agent1', False, False]
        mockGetDate = mocker.patch.object(KMeansManager, 'getPubDateFloat')
        mockGetDate.side_effect = [1900, False, 1901]
        mockGetDate = mocker.patch.object(KMeansManager, 'getEditionStatement')
        mockGetDate.side_effect = ['ed1', 'ed2', False]

        mockDF = mocker.patch('managers.kMeans.pd')
        mockFrame = mocker.MagicMock()
        mockDF.DataFrame.return_value = mockFrame
        mockFrame.index = [i for i in range(1200)]

        testModel.createDF()

        assert testModel.maxK == int(1200 * (2/9))

    def test_createDF_maxK_500_1000(self, mocker, testModel):
        mockGetPub = mocker.patch.object(KMeansManager, 'getPublisher')
        mockGetPub.side_effect = ['agent1', False, False]
        mockGetDate = mocker.patch.object(KMeansManager, 'getPubDateFloat')
        mockGetDate.side_effect = [1900, False, 1901]
        mockGetDate = mocker.patch.object(KMeansManager, 'getEditionStatement')
        mockGetDate.side_effect = ['ed1', 'ed2', False]

        mockDF = mocker.patch('managers.kMeans.pd')
        mockFrame = mocker.MagicMock()
        mockDF.DataFrame.return_value = mockFrame
        mockFrame.index = [i for i in range(750)]

        testModel.createDF()

        assert testModel.maxK == int(750 * (3/9))

    def test_createDF_maxK_250_500(self, mocker, testModel):
        mockGetPub = mocker.patch.object(KMeansManager, 'getPublisher')
        mockGetPub.side_effect = ['agent1', False, False]
        mockGetDate = mocker.patch.object(KMeansManager, 'getPubDateFloat')
        mockGetDate.side_effect = [1900, False, 1901]
        mockGetDate = mocker.patch.object(KMeansManager, 'getEditionStatement')
        mockGetDate.side_effect = ['ed1', 'ed2', False]

        mockDF = mocker.patch('managers.kMeans.pd')
        mockFrame = mocker.MagicMock()
        mockDF.DataFrame.return_value = mockFrame
        mockFrame.index = [i for i in range(350)]

        testModel.createDF()

        assert testModel.maxK == int(350 * (4/9))

    def test_getPubDateFloat_range(self, mocker):
        mockDates = ['2000|other_date', '1900-1901|publication_date']
        outYear = KMeansManager.getPubDateFloat(mockDates)
        assert outYear == 1900.5
    
    def test_getPubDateFloat_year_only(self, mocker):
        mockDates = ['2000|other_date', '1900|publication_date']
        outYear = KMeansManager.getPubDateFloat(mockDates)
        assert outYear == 1900

    def test_getPubDateFloat_full_date(self, mocker):
        mockDates = ['1900-01-01|publication_date']
        outYear = KMeansManager.getPubDateFloat(mockDates)
        assert outYear == 1900
    
    def test_getPubDateFloat_neither(self, mocker):
        mockDates = ['2000|other_date', '1900-1901|pub_date']
        outYear = KMeansManager.getPubDateFloat(mockDates)
        assert outYear == 0
    
    def test_getPubDateFloat_no_dates(self, mocker):
        outYear = KMeansManager.getPubDateFloat([])
        assert outYear == 0
    
    def test_getPubDateFloat_bad_value(self, mocker):
        outYear = KMeansManager.getPubDateFloat(['2000'])
        assert outYear == 0

    def test_getPubDateFloat_bad_string_value(self, mocker):
        outYear = KMeansManager.getPubDateFloat(['test|date'])
        assert outYear == 0

    def test_getPublisher_clean(self, mocker):
        outPublisher = KMeansManager.getPublisher('Test|||')

        assert outPublisher == 'test'
    
    def test_getPublisher_stripped(self, mocker):
        outPublisher = KMeansManager.getPublisher('Test Second [].||viaf|')

        assert outPublisher == 'test second'
    
    def test_getPublisher_none(self, mocker):
        outPublisher = KMeansManager.getPublisher(None)

        assert outPublisher == ''

    def test_getEditionStatement_value_present(self, mocker):
        edStmt = KMeansManager.getEditionStatement(['edition|1'])

        assert edStmt == 'edition'

    def test_getEditionStatement_no_value(self, mocker):
        edStmt = KMeansManager.getEditionStatement(None)

        assert edStmt == ''

    def test_getEditionStatement_empty_array(self, mocker):
        edStmt = KMeansManager.getEditionStatement([])

        assert edStmt == ''
    
    def test_generateClusters_multiple(self, mocker, testModel):
        mockGetK = mocker.patch.object(KMeansManager, 'getK')
        testModel.k = 2
        testModel.maxK = 3

        mockCluster = mocker.patch.object(KMeansManager, 'cluster')
        mockCluster.return_value = [
            0, 1, 0
        ]

        testModel.df = pd.DataFrame(['row1', 'row2', 'row3'])

        testModel.generateClusters()
        assert testModel.clusters[0][0].iloc[0][0] == 1900
        assert testModel.clusters[0][1].iloc[0][0] == 1900
        assert testModel.clusters[1][0].iloc[0][0] == 2000
    
    def test_generateClusters_single(self, mocker, testModel):
        mockGetK = mocker.patch.object(KMeansManager, 'getK')
        mockGetK.side_effect = ZeroDivisionError

        mockCluster = mocker.patch.object(KMeansManager, 'cluster')
        mockCluster.side_effect = ValueError
        testModel.instances = ['row1']
        testModel.df = pd.DataFrame(['row1'])
        testModel.maxK = 3

        testModel.generateClusters()
        assert testModel.clusters[0][0].iloc[0][0] == 1900

    def test_cluster_score(self, mocker, testModel):
        mockPipeline = mocker.MagicMock()
        mockPipeline.fit_transform.return_value = 'testLabels'

        mockCreate = mocker.patch.object(KMeansManager, 'createPipeline')
        mockCreate.return_value = mockPipeline
        mockGetColumns = mocker.patch.object(KMeansManager, 'getDataColumns')
        mockSilhouette = mocker.patch('managers.kMeans.silhouette_score')
        mockSilhouette.return_value = 1

        out = testModel.cluster(1, score=True)
        assert out == 1
        mockGetColumns.assert_called_once()
        mockPipeline.set_params.assert_called_once_with(kmeans=None)
        mockPipeline.fit_transform.assert_called_once()
        mockSilhouette.assert_called_once()
    
    def test_cluster_predict(self, mocker, testModel):
        mockPipeline = mocker.MagicMock()
        mockCreate = mocker.patch.object(KMeansManager, 'createPipeline')
        mockGetColumns = mocker.patch.object(KMeansManager, 'getDataColumns')
        mockCreate.return_value = mockPipeline

        testModel.cluster(1)
        mockCreate.assert_called_once()
        mockGetColumns.assert_called_once()
        mockPipeline.fit_predict.assert_called_once()

    def test_parseEditions(self, testModel):
        outEditions = testModel.parseEditions()
        assert len(outEditions) == 3
        assert outEditions[1][0] == 1950
