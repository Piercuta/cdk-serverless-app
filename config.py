from dataclasses import dataclass
from typing import Dict, Any
import os


@dataclass
class Config:
    # AWS Configuration
    AWS_ACCOUNT: str = "532673134317"
    AWS_REGION: str = "eu-west-1"

    # Frontend Configuration
    DOMAIN_NAME: str = "react.piercuta.com"
    HOSTED_ZONE_ID: str = "Z0068506UV3AK4JBKP59"
    ZONE_NAME: str = "piercuta.com"
    CERTIFICATE_ARN: str = "arn:aws:acm:us-east-1:532673134317:certificate/0755fa69-6f18-451a-8987-d98c395089b9"

    # Lambda Configuration
    LAMBDA_MEMORY_SIZE: int = 512
    LAMBDA_TIMEOUT: int = 30

    # GitHub Configuration
    GITHUB_SECRET_NAME: str = "github-token"
    GITHUB_SECRET_JSON_FIELD: str = "token"
    GITHUB_OWNER: str = "Piercuta"
    GITHUB_REPO: str = "react-sample"
    GITHUB_BRANCH: str = "main"

    @classmethod
    def get_env(cls) -> Dict[str, Any]:
        return {
            "account": os.getenv('AWS_ACCOUNT', cls.AWS_ACCOUNT),
            "region": os.getenv('AWS_REGION', cls.AWS_REGION)
        }

    @classmethod
    def get_domain_name(cls) -> str:
        return os.getenv('DOMAIN_NAME', cls.DOMAIN_NAME)

    @classmethod
    def get_hosted_zone_id(cls) -> str:
        return os.getenv('HOSTED_ZONE_ID', cls.HOSTED_ZONE_ID)

    @classmethod
    def get_zone_name(cls) -> str:
        return os.getenv('ZONE_NAME', cls.ZONE_NAME)

    @classmethod
    def get_certificate_arn(cls) -> str:
        return os.getenv('CERTIFICATE_ARN', cls.CERTIFICATE_ARN)

    @classmethod
    def get_lambda_memory_size(cls) -> int:
        return os.getenv('LAMBDA_MEMORY_SIZE', cls.LAMBDA_MEMORY_SIZE)

    @classmethod
    def get_lambda_timeout(cls) -> int:
        return os.getenv('LAMBDA_TIMEOUT', cls.LAMBDA_TIMEOUT)

    @classmethod
    def get_github_secret_name(cls) -> str:
        return os.getenv('GITHUB_SECRET_NAME', cls.GITHUB_SECRET_NAME)

    @classmethod
    def get_github_secret_json_field(cls) -> str:
        return os.getenv('GITHUB_SECRET_JSON_FIELD', cls.GITHUB_SECRET_JSON_FIELD)

    @classmethod
    def get_github_owner(cls) -> str:
        return os.getenv('GITHUB_OWNER', cls.GITHUB_OWNER)

    @classmethod
    def get_github_repo(cls) -> str:
        return os.getenv('GITHUB_REPO', cls.GITHUB_REPO)

    @classmethod
    def get_github_branch(cls) -> str:
        return os.getenv('GITHUB_BRANCH', cls.GITHUB_BRANCH)
