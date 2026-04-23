"""Utility helpers for OpenAI client creation and data processing."""

from typing import Any, Dict

import pandas as pd
import structlog
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from config.settings import settings

# Module-level logger for this module
logger = structlog.get_logger(__name__)


def get_openai_client() -> AzureOpenAI:
    """Create and return a configured AzureOpenAI client.

    Returns:
        AzureOpenAI: Configured client for the project's Azure OpenAI endpoint.

    Notes:
        - `DefaultAzureCredential` is instantiated with
          `exclude_managed_identity_credential=True` to prefer developer credentials
          (e.g. Azure CLI) during local development.
        - The returned client is constructed with `azure_endpoint` and `api_version`
          from the project's settings and additional authentication parameters.
    """
    client_args: Dict[str, Any] = {}

    # Use an Azure OpenAI endpoint,
    # either with a key or with keyless authentication
    if settings.azure_openai_apikey:
        # Authenticate using an Azure OpenAI API key
        # This is generally discouraged, but is provided for developers
        # that want to develop locally inside the Docker container.
        client_args["api_key"] = settings.azure_openai_apikey.get_secret_value()
        logger.info("Azure OpenAI authentication through: api key")
    else:
        credential = DefaultAzureCredential(exclude_managed_identity_credential=True)
        logger.info(
            "Azure OpenAI authentication through: ChainedTokenCredentials (managed or azure cli)"
        )
        client_args["azure_ad_token_provider"] = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )

    return AzureOpenAI(
        azure_endpoint=str(settings.openai_endpoint),
        api_version=settings.llm.API_version,
        **client_args,
    )



