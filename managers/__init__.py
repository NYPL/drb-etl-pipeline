# Managers Necessary for API, must always be available
from .db import DBManager
from .redis import RedisManager
from .elasticsearch import ElasticsearchManager

# Managers for other processes, can be skipped for API
try:
    from .coverManager import CoverManager
    from .doabParser import DOABLinkManager
    from .gutenberg import GutenbergManager
    from .kMeans import KMeansManager
    from .oclcCatalog import OCLCCatalogManager
    from .oclcClassify import ClassifyManager
    from .nyplApi import NyplApiManager
    from .webpubManifest import WebpubManifest
    from .rabbitmq import RabbitMQManager
    from .sfrRecord import SFRRecordManager
    from .sfrElasticRecord import SFRElasticRecordManager
    from .s3 import S3Manager
    from .smartsheet import SmartSheetManager
except (ModuleNotFoundError, ImportError):
        print('Unable to import module, skipping non-API managers')
