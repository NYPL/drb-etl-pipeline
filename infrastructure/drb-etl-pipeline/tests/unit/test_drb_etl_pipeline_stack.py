import aws_cdk as core
import aws_cdk.assertions as assertions

from drb_etl_pipeline.drb_etl_pipeline_stack import DrbEtlPipelineStack

# example tests. To run these tests, uncomment this file along with the example
# resource in drb_etl_pipeline/drb_etl_pipeline_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DrbEtlPipelineStack(app, "drb-etl-pipeline")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
