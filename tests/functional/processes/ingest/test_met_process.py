from processes import METProcess
from .assert_ingested_records import assert_ingested_records
from managers.s3 import S3Manager, S3Error


def test_met_process():

    met_process = METProcess('complete', None, None, None, 5, None)

    met_process.runProcess()
    records = assert_ingested_records(source_name='met')

    
    s3_manager = S3Manager()
    s3_manager.createS3Client() 

    s3_bucket_name = 'drb-files-local'
    for record in records:
        pdf_key = f"manifests/{record.id}.pdf"

        try:
            s3_manager.getObjectFromBucket(pdf_key, s3_bucket_name)
        except S3Error as e:
            assert False, f"PDF manifest for record {record.id} does not exist in S3: {e.message}"
        except Exception as e:
            assert False, f"An error occurred while checking for the PDF manifest: {str(e)}"
