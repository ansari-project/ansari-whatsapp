# Service Provider for ansari-whatsapp
"""Factory function for providing the appropriate Ansari client implementation."""

from loguru import logger

from ansari_whatsapp.utils.config import get_settings
from ansari_whatsapp.services.ansari_client_base import AnsariClientBase
from ansari_whatsapp.services.ansari_client_real import AnsariClientReal
from ansari_whatsapp.services.ansari_client_mock import AnsariClientMock


def get_ansari_client() -> AnsariClientBase:
    """Factory function that returns the appropriate Ansari client based on configuration.

    This function implements the Service Provider pattern, returning either:
    - AnsariClientReal: Makes actual HTTP calls to the backend (production/integration testing)
    - AnsariClientMock: Simulates backend responses without network calls (unit testing/offline dev)

    The choice is controlled by the MOCK_ANSARI_CLIENT environment variable.

    Returns:
        AnsariClientBase: Either AnsariClientReal or AnsariClientMock instance

    Example:
        >>> client = get_ansari_client()
        >>> result = await client.register_user("+1234567890", "en")
    """
    settings = get_settings()

    if settings.MOCK_ANSARI_CLIENT:
        logger.info("Service Provider: Returning AnsariClientMock (mock mode enabled)")
        return AnsariClientMock()
    else:
        logger.debug("Service Provider: Returning AnsariClientReal (production mode)")
        return AnsariClientReal()
