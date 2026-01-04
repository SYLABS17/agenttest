"""Factory for creating cloud provider instances."""

from typing import Literal, Optional
import structlog

from src.cloud.common.interfaces import CloudProvider

logger = structlog.get_logger(__name__)

CloudType = Literal["azure", "gcp", "aws"]


def create_cloud_provider(
    cloud_type: CloudType,
    config: Optional[dict] = None,
) -> CloudProvider:
    """
    Factory function to create cloud provider instance.

    Args:
        cloud_type: Cloud provider type (azure, gcp, aws)
        config: Optional configuration override

    Returns:
        CloudProvider instance for the specified cloud

    Raises:
        ValueError: If cloud_type is not supported
    """
    logger.info("creating_cloud_provider", cloud_type=cloud_type)

    if cloud_type == "azure":
        from src.cloud.azure import AzureCloudProvider
        return AzureCloudProvider(config)

    elif cloud_type == "gcp":
        from src.cloud.gcp import GCPCloudProvider
        return GCPCloudProvider(config)

    elif cloud_type == "aws":
        from src.cloud.aws import AWSCloudProvider
        return AWSCloudProvider(config)

    else:
        raise ValueError(f"Unsupported cloud provider: {cloud_type}")


def get_default_provider() -> CloudProvider:
    """
    Get the default cloud provider based on environment.

    Checks for cloud-specific environment variables to determine
    which provider to use.
    """
    import os

    # Check for Azure
    if os.getenv("AZURE_SEARCH_ENDPOINT"):
        return create_cloud_provider("azure")

    # Check for GCP
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        return create_cloud_provider("gcp")

    # Check for AWS
    if os.getenv("AWS_REGION"):
        return create_cloud_provider("aws")

    # Default to Azure
    logger.warning("no_cloud_detected", default="azure")
    return create_cloud_provider("azure")
