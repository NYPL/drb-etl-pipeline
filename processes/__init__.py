# API process should always be available
from .api import APIProcess

# Other processes may be skipped
try:
    from .covers import CoverProcess
    from .doab import DOABProcess
    from .gutenberg import GutenbergProcess
    from .hathiTrust import HathiTrustProcess
    from .nypl import NYPLProcess
    from .oclcCatalog import CatalogProcess
    from .oclcClassify import ClassifyProcess
    from .sfrCluster import ClusterProcess
    from .developmentSetup import DevelopmentSetupProcess
    from .s3Files import S3Process
    from .muse import MUSEProcess
    from .ingestReport import IngestReportProcess
    from .met import METProcess
    from .migration import MigrationProcess
except (ModuleNotFoundError, ImportError):
    print('Skipping non-API processes')
