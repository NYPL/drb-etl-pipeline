# Managers Necessary for API, must always be available
from .db import DBManager
from .redis import RedisManager
from .elasticsearch import ElasticsearchManager
from .nyplApi import NyplApiManager
from .rabbitmq import RabbitMQManager
from .s3 import S3Manager

# Managers for other processes, can be skipped for API
try:
    from .coverManager import CoverManager
    from .doabParser import DOABLinkManager
    from .gutenberg import GutenbergManager
    from .kMeans import KMeansManager
    from .oclcCatalog import OCLCCatalogManager
    from .oclcClassify import ClassifyManager
    from .webpubManifest import WebpubManifest
    from .sfrRecord import SFRRecordManager
    from .sfrElasticRecord import SFRElasticRecordManager
    from .smartsheet import SmartSheetManager
except (ModuleNotFoundError, ImportError):
        print('Unable to import module, skipping non-API managers')
