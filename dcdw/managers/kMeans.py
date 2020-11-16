from collections import defaultdict
from math import sqrt
import re
import string
import warnings

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans
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
    
    def createPipeline(self):
        return Pipeline([
            ('union', FeatureUnion(
                transformer_list=[
                    ('place', Pipeline([
                        ('selector', TextSelector(key='place')),
                        ('tfidf', TfidfVectorizer(
                            preprocessor=KMeansManager.pubProcessor,
                            stop_words='english',
                            strip_accents='unicode',
                            analyzer='char_wb',
                            ngram_range=(2,4))
                        )
                    ])),
                    ('publisher', Pipeline([
                        ('selector', TextSelector(key='publisher')),
                        ('tfidf', TfidfVectorizer(
                            preprocessor=KMeansManager.pubProcessor,
                            stop_words='english',
                            strip_accents='unicode',
                            analyzer='char_wb',
                            ngram_range=(2,4))
                        )
                    ])),
                    ('edition', Pipeline([
                        ('selector', TextSelector(key='edition')),
                        ('tfidf', TfidfVectorizer(
                            preprocessor=KMeansManager.pubProcessor,
                            stop_words='english',
                            strip_accents='unicode',
                            analyzer='char_wb',
                            ngram_range=(1,3))
                        )
                    ])),
                    ('date', Pipeline([
                        ('selector', NumberSelector(key='pubDate')),
                        ('scaler', MinMaxScaler())
                    ]))
                ],
                transformer_weights={
                    'place': 0.5,
                    'publisher': 1.0,
                    'edition': 0.75,
                    'date': 2.0 
                }
            )),
            ('kmeans', KMeans(
                n_clusters=self.currentK,
                n_jobs=-1
            ))
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
            print('Cleaned string {} to {} for processing'.format(
                raw, cleanStr
            ))
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
        if self.maxK > 1000:
            self.maxK = int(self.maxK * (2/9))
        elif self.maxK > 500:
            self.maxK = int(self.maxK * (3/9))
        elif self.maxK > 250:
            self.maxK = int(self.maxK * (4/9))
    
    @staticmethod
    def emptyInstance(instance):
        print(instance.spatial, instance.dates, instance.publisher)
        return bool(instance.spatial or\
            KMeansManager.getPubDateFloat(instance.dates) or\
            KMeansManager.getPublisher(instance.publisher))

    @classmethod
    def getPubDateFloat(cls, dates):
        pubYears = {}
        if not dates:
            return 0
        for d in dates:
            print(d)
            try:
                date, dateType = tuple(d.split('|'))
            except ValueError:
                return 0
            dateStr = str(date).strip('];.,- ')
            if re.match(r'[0-9]{4}-[0-9]{4}', dateStr):
                startYear, endYear = tuple(dateStr.split('-'))
                pubYears[dateType] = (int(startYear) + int(endYear)) / 2
            elif re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', dateStr):
                year, month, day = tuple(dateStr.split('-'))
                pubYears[dateType] = year
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
            return None
        for version in hasVersion:
            print(version)
            statement, editionNo = tuple(version.split('|'))
            return statement
        
        return ''
    
    def generateClusters(self):
        print('Generating Clusters from instances')
        try:
            # Calculate the step for the first run at determining k
            # Use the natural log of the value to get a reasonable scale
            # for different values
            step = int(np.log(self.maxK)**1.5 - 1) if np.log(self.maxK) > 1.6 else 1
            # First pass at finding best value for k, using the step value
            # derived above
            self.getK(1, self.maxK, step)
            # Get narrower band of possible k values, based off the initial
            # step value
            startK = self.k - (step - 1) if self.k > (step - 1) else 1
            stopK = self.k + step if (self.k + step) <= self.maxK else self.maxK
            # Get the final k value by iterating through the much narrower
            # range returned above
            self.getK(startK, stopK, 1)
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
    
    def getK(self, start, stop, step):
        print('Calculating number of clusters, max {}'.format(
            self.maxK
        ))
        warnings.filterwarnings('error', category=ConvergenceWarning)
        wcss = []
        for i in range(start, stop, step):
            try:
                wcss.append((self.cluster(i, score=True), i))
            except ConvergenceWarning:
                print('Exceeded number of distinct clusters, break')
                break
            except ValueError:
                self.k = 1
                return None
        
        x1, y1 = wcss[0][1], wcss[0][0]
        x2, y2 = wcss[len(wcss) - 1][1], wcss[(len(wcss) - 1)][0]

        distances = []
        denominator = sqrt((y2 - y1)**2 + (x2 - x1)**2)
        for i in range(len(wcss)):
            x0 = i + 1
            y0 = wcss[i][0]

            numerator = abs((y2 - y1)*x0 - (x2 - x1)*y0 + x2*y1 - y2*x1)
            distances.append(numerator/denominator)
        
        finalStart = 1 if start < 2 else start + 1 
        self.k = distances.index(max(distances)) + finalStart
        return None
    
    def cluster(self, k, score=False):
        self.currentK = k
        print('Generating cluster for k={}'.format(k))
        pipeline = self.createPipeline()
        if score is True:
            print('Returning score for n_clusters estimation')
            pipeline.fit(self.df)
            return pipeline['kmeans'].inertia_
        else:
            print('Returning model prediction')
            return pipeline.fit_predict(self.df)
    
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