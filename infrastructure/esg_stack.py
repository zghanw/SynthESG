"""
SynthESG — AWS CDK Infrastructure Stack.

Provisions:
- S3 bucket for frontend static hosting
- CloudFront distribution for global CDN delivery
- S3 bucket for exported JSON reports (private)

No database or auth infrastructure — the app is stateless.
"""

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
)
from constructs import Construct


class SynthESGStack(Stack):
    """Main infrastructure stack for SynthESG."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Frontend S3 Bucket ──────────────────────────────
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── CloudFront Distribution ─────────────────────────
        # Serves the frontend globally with HTTPS and caching.
        oac = cloudfront.S3OriginAccessControl(
            self, "FrontendOAC",
            description="SynthESG frontend OAC",
        )

        distribution = cloudfront.Distribution(
            self, "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    frontend_bucket,
                    origin_access_control=oac,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_page_path="/index.html",
                    response_http_status=200,
                ),
            ],
        )

        # ── Reports Bucket (private) ────────────────────────
        reports_bucket = s3.Bucket(
            self, "ReportsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── Outputs ────────────────────────────────────────
        CfnOutput(
            self, "FrontendUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="SynthESG frontend URL (CloudFront)",
        )
        CfnOutput(
            self, "FrontendBucketName",
            value=frontend_bucket.bucket_name,
            description="S3 bucket — upload frontend files here",
        )
        CfnOutput(
            self, "ReportsBucketName",
            value=reports_bucket.bucket_name,
            description="S3 bucket for exported JSON reports",
        )
