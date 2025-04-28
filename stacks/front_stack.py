from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_iam as iam,
    aws_certificatemanager as acm,
    RemovalPolicy,
    SecretValue,
    CfnOutput
)
from constructs import Construct
from config import Config


class FrontStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api_url: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Récupération de la zone hébergée
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone",
            hosted_zone_id=Config.get_hosted_zone_id(),
            zone_name=Config.get_zone_name()
        )

        # Récupération du certificat
        certificate = acm.Certificate.from_certificate_arn(
            self, "Certificate",
            certificate_arn=Config.get_certificate_arn()
        )

        # Création du bucket S3 pour l'application
        website_bucket = s3.Bucket(
            self, "WebsiteBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            # public_read_access=True,  # Permet l'accès public en lecture
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Bloque l'accès public direct
        )

        # Création de l'origine S3 pour CloudFront
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "WebsiteOAI",
            comment="Access identity for website bucket"
        )

        # Ajout des permissions pour l'OAI
        website_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[website_bucket.arn_for_objects("*")],
                principals=[iam.CanonicalUserPrincipal(
                    origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id)]
            )
        )

        # Création de la distribution CloudFront
        distribution = cloudfront.Distribution(
            self, "WebsiteDistribution",
            default_root_object="index.html",
            domain_names=[Config.get_domain_name()],
            certificate=certificate,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_identity(
                    website_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                compress=True,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            )
        )

        # Création du record set
        record_set = route53.ARecord(
            self, "ReactFrontRecord",
            zone=hosted_zone,
            record_name=Config.get_domain_name().split('.')[0],  # Extrait 'react' de 'react.piercuta.com'
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution)
            )
        )

        # Création du projet CodeBuild
        build_project = codebuild.PipelineProject(
            self, "ReactBuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": [
                            "npm install",
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            'echo "REACT_APP_API_URL=$REACT_APP_API_URL" > .env',
                        ]
                    },
                    "build": {
                        "commands": [
                            "npm run build",
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "aws s3 sync build/ s3://${WEBSITE_BUCKET} --delete",
                            "aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} --paths '/*'"
                        ]
                    }
                }
            }),
        )

        # Ajout des permissions nécessaires au projet CodeBuild
        website_bucket.grant_read_write(build_project)
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudfront:CreateInvalidation"],
                resources=[distribution.distribution_arn],
            )
        )

        # Création du pipeline
        pipeline = codepipeline.Pipeline(
            self, "WebsitePipeline",
            pipeline_name="react-website-pipeline",
            artifact_bucket=s3.Bucket(
                self, "PipelineArtifactBucket",
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True
            )
        )

        # Ajout des permissions pour accéder au secret GitHub
        pipeline.role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                # resources=["arn:aws:secretsmanager:eu-west-1:647408608766:secret:github-token-*"],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        # Source stage
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner=Config.get_github_owner(),
            repo=Config.get_github_repo(),
            branch=Config.get_github_branch(),
            oauth_token=SecretValue.secrets_manager(
                Config.get_github_secret_name(),
                json_field=Config.get_github_secret_json_field()
            ),
            output=source_output,
        )

        # Build stage
        build_output = codepipeline.Artifact()
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=build_project,
            input=source_output,
            outputs=[build_output],
            environment_variables={
                "WEBSITE_BUCKET": codebuild.BuildEnvironmentVariable(
                    value=website_bucket.bucket_name
                ),
                "CLOUDFRONT_DISTRIBUTION_ID": codebuild.BuildEnvironmentVariable(
                    value=distribution.distribution_id
                ),
                "REACT_APP_API_URL": codebuild.BuildEnvironmentVariable(
                    value=api_url[:-1]
                ),
            },
        )

        # Ajout des stages au pipeline
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action],
        )
        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action],
        )

        # Output l'URL de l'API
        CfnOutput(
            self, "ReactFrontUrl",
            value=distribution.domain_name,
            description="URL de l'application React"
        )

        CfnOutput(
            self, "ReactRecordName",
            value=record_set.domain_name,
            description="Nom du record de l'application React"
        )
