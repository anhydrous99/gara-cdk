"""Secrets construct for AWS Secrets Manager references"""
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

from gara_cdk.config import SecretsConfig


class SecretsConstruct(Construct):
    """
    Construct for referencing existing secrets in AWS Secrets Manager.

    References (does not create) existing secrets for GitHub token and API key.
    These secrets must be created manually before deploying the stack.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: SecretsConfig
    ) -> None:
        """
        Initialize the secrets construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            config: Secrets configuration settings
        """
        super().__init__(scope, construct_id)

        self._github_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GithubToken",
            config.github_token_secret_name
        )

        self._api_key_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "ApiKey",
            config.api_key_secret_name
        )

        self._config = config

    @property
    def github_secret(self) -> secretsmanager.ISecret:
        """Get the GitHub token secret reference"""
        return self._github_secret

    @property
    def api_key_secret(self) -> secretsmanager.ISecret:
        """Get the API key secret reference"""
        return self._api_key_secret

    @property
    def github_token_json_key(self) -> str:
        """Get the JSON key for GitHub token in the secret"""
        return self._config.github_token_json_key

    @property
    def api_key_secret_name(self) -> str:
        """Get the name of the API key secret"""
        return self._config.api_key_secret_name
