from collections import defaultdict
from math import sqrt
import re
import string
import warnings

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import MinMaxScaler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.exceptions import ConvergenceWarning


class TextSelector(BaseEstimator, TransformerMixin):
    def __init__(self, key):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.key]


class NumberSelector(BaseEstimator, TransformerMixin):
    def __init__(self, key):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[[self.key]]


class KMeansManager:
    def __init__(self, instances):
        self.instances = instances
        self.df = None
        self.clusters = defaultdict(list)
    
    def createPipeline(self, transformers):
        pipelineComponents = {
            'place': ('place', Pipeline([
                ('selector', TextSelector(key='place')),
                ('tfidf', TfidfVectorizer(
                    preprocessor=KMeansManager.pubProcessor,
                    stop_words='english',
                    strip_accents='unicode',
                    analyzer='char_wb',
                    ngram_range=(2,4))
                )
            ])),
            'publisher': ('publisher', Pipeline([
                ('selector', TextSelector(key='publisher')),
                ('tfidf', TfidfVectorizer(
                    preprocessor=KMeansManager.pubProcessor,
                    stop_words='english',
                    strip_accents='unicode',
                    analyzer='char_wb',
                    ngram_range=(2,4))
                )
            ])),
            'edition': ('edition', Pipeline([
                ('selector', TextSelector(key='edition')),
                ('tfidf', TfidfVectorizer(
                    preprocessor=KMeansManager.pubProcessor,
                    stop_words='english',
                    strip_accents='unicode',
                    analyzer='char_wb',
                    ngram_range=(1,3))
                )
            ])),
            'pubDate': ('pubDate', Pipeline([
                ('selector', NumberSelector(key='pubDate')),
                ('scaler', MinMaxScaler())
            ]))
        }

        pipelineWeights = {
            'place': 0.5,
            'publisher': 1.0,
            'edition': 0.75,
            'pubDate': 2.0 
        }

        return Pipeline([
            ('union', FeatureUnion(
                transformer_list=[pipelineComponents[t] for t in transformers],
                transformer_weights={t: pipelineWeights[t] for t in transformers}
            )),
            ('kmeans', KMeans(n_clusters=self.currentK, max_iter=150, n_init=5))
        ])
    
    @classmethod
    def pubProcessor(cls, raw):
        if isinstance(raw, list):
            raw = ', '.join(filter(None, raw))
        if raw is not None:
            raw = raw.replace('&', 'and')
            cleanStr = raw.translate(
                str.maketrans('', '', string.punctuation)
            ).lower()
            cleanStr = cleanStr\
                .replace('sn', '')\
                .replace('place of publication not identified', '')\
                .replace('publisher not identified', '')
            cleanStr = re.sub(r'\s+', ' ', cleanStr)
            return cleanStr
        print('Unable to clean NoneType, returning empty string')
        return ''

    def createDF(self):
        print('Generating DataFrame from instance data')
        self.df = pd.DataFrame([
            {
                'place': i.spatial if i.spatial else '',
                'publisher': KMeansManager.getPublisher(i.publisher),
                'pubDate': KMeansManager.getPubDateFloat(i.dates),
                'edition': KMeansManager.getEditionStatement(i.has_version),
                'uuid': i.uuid
            }
            for i in self.instances
            if KMeansManager.emptyInstance(i) != False
        ])
        self.maxK = len(self.df.index) if len(self.df.index) > 1 else 2
        if self.maxK > 5000:
            self.maxK = int(self.maxK * (1/9))
        elif self.maxK > 1000:
            self.maxK = int(self.maxK * (2/9))
        elif self.maxK > 500:
            self.maxK = int(self.maxK * (3/9))
        elif self.maxK > 250:
            self.maxK = int(self.maxK * (4/9))
    
    @staticmethod
    def emptyInstance(instance):
        return bool(instance.spatial or\
            KMeansManager.getPubDateFloat(instance.dates) or\
            KMeansManager.getPublisher(instance.publisher))

    @classmethod
    def getPubDateFloat(cls, dates):
        pubYears = {}
        if not dates:
            return 0
        for d in dates:
            try:
                date, dateType = tuple(d.split('|'))
            except ValueError:
                return 0
            dateStr = str(date).strip('];:.,- ')
            if re.match(r'[0-9]{4}-[0-9]{4}', dateStr):
                rangeMatches = re.match(r'([0-9]{4})-([0-9]{4})', dateStr)
                startYear = rangeMatches.group(1)
                endYear = rangeMatches.group(2)
                pubYears[dateType] = (int(startYear) + int(endYear)) / 2
            elif re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', dateStr):
                year, month, day = tuple(dateStr.split('-'))
                pubYears[dateType] = int(year)
            else:
                try:
                    dateInt = int(dateStr)
                    pubYears[dateType] = dateInt
                except ValueError:
                    pass

        for datePref in ['copyright_date', 'publication_date']:
            if datePref in pubYears.keys():
                return pubYears[datePref]
        
        print('Unable to locate publication date')
        return 0
    
    @classmethod
    def getPublisher(cls, pubStr):
        if not pubStr:
            return ''
        publisher, *_ = tuple(pubStr.split('|'))
        return publisher.strip(',. []').lower()

    @classmethod
    def getEditionStatement(cls, hasVersion):
        if not hasVersion:
            return ''
        for version in hasVersion:
            try:
                statement, _ = tuple(version.split('|'))
                return statement
            except ValueError:
                pass
        
        return ''
    
    def generateClusters(self):
        print('Generating Clusters from instances')
        try:
            print('Calculating number of clusters, max {}'.format(
                self.maxK
            ))
            self.getK(2, self.maxK)
            print('Setting K to {}'.format(self.k))
        except ZeroDivisionError:
            print('Single instance found setting K to 1')
            self.k = 1
        
        try:
            labels = self.cluster(self.k)
        except ValueError as err:
            labels = [0] * len(self.instances)
        
        for n, item in enumerate(labels):
            try:
                self.clusters[item].append(self.df.loc[[n]])
            except KeyError:
                continue
    
    def getK(self, start, stop):
        warnings.filterwarnings('error', category=ConvergenceWarning)

        startScore = 0
        stopScore = 0

        prevStart = 0
        prevStop = 0

        while True:
            middle = int((stop + start)/2)

            print(start, stop, middle)

            try:
                if start != prevStart: startScore = self.cluster(start, score=True) 
            except (ValueError, ConvergenceWarning):
                print('Exceeded number of distinct clusters, break')
                start = 1
                startScore = 1
                break

            try:
                if stop != prevStop: stopScore = self.cluster(stop, score=True) 
            except (ValueError, ConvergenceWarning):
                print('Exceeded number of distinct clusters, break')
                stop = middle
                continue

            if stop - start <= 1:
                break

            prevStart = start
            prevStop = stop

            if startScore > stopScore:
                stop = middle
            else:
                start = middle

        self.k = start if startScore > stopScore else stop

    def cluster(self, k, score=False):
        self.currentK = k
        print('Generating cluster for k={}'.format(k))
        columnsWithData = self.getDataColumns()
        pipeline = self.createPipeline(columnsWithData)

        labels = pipeline.fit_predict(self.df)

        if score is True:
            pipeline.set_params(kmeans=None)
            X = pipeline.fit_transform(self.df)
            return silhouette_score(X, labels)
        else:
            print('Returning model prediction')
            return labels

    def getDataColumns(self):
        dataColumns = []
        for colName in self.df.columns:
            if colName == 'uuid': continue

            hasValue = self.df[colName] != ''
            if len(list(filter(lambda x: x is True, list(hasValue.head())))) > 0:
                dataColumns.append(colName)
        
        return dataColumns
    
    def parseEditions(self):
        eds = []
        print('Generating editions from clusters')
        for clust in dict(self.clusters):
            yearEds = defaultdict(list)
            print('Parsing cluster {}'.format(clust))
            for ed in self.clusters[clust]:
                print('Adding instance to {} edition'.format(
                    ed.iloc[0]['pubDate']
                ))
                yearEds[ed.iloc[0]['pubDate']].append(ed.iloc[0]['uuid'])
            eds.extend([(year, data) for year, data in yearEds.items()])
            eds.sort(key=lambda x: x[0])

        return eds