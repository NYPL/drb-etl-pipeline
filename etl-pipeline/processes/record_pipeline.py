

'''
High-Level Flow:

1. Ingestors get and map records and send message to record pipeline queue
2. Record pipeline process processes messages from the queue
3. For each message, the record pipeline stores the files, frbrizes and clusters the record
4. Optionally, the process fulfills the links

Pros: 
- Scalability: We can spin up n tasks to process messages from the queue. 
- Simplicity: Removes potentially 4 processes and ECS tasks
- Testability: Possible to test 
- Observability/Debuggability: Easier to see where a record fails to be processed in the pipeline
- State Management: We can ensure the database state fields truthfully match the state of a record. 
'''

class RecordPipelineProcess:

    def __init__(self):
        pass

    def run():
        pass
        # 1. Read message from queue

        # 2. Store/add files

        # 3. FRBRize record

        # 4. Cluster record

        # 5. Optionally fulfill links
