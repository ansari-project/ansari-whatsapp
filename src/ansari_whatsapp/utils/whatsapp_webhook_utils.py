# WhatsApp Webhook Utilities
"""Utilities for handling webhook operations between Meta and our server.

This module contains functions for:
- Parsing webhook payloads received from Meta
- Verifying webhook signatures for security
- Creating standardized responses for Meta
"""

import hmac
import hashlib
from loguru import logger
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, Response

from ansari_whatsapp.utils.config import get_settings

settings = get_settings()


def _verify_signature_with_secret(secret: str, body_bytes: bytes, received_signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature with a single app secret.

    Args:
        secret: The app secret string
        body_bytes: Raw request body bytes
        received_signature: The signature received from the X-Hub-Signature-256 header

    Returns:
        bool: True if signature matches, False otherwise
    """
    app_secret = secret.encode('utf-8')
    computed_signature = hmac.new(app_secret, body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_signature, received_signature)


def _verify_signature_multi(secrets_str: str, body_bytes: bytes, received_signature: str) -> bool:
    """
    Verify signature with multiple comma-separated app secrets (temporary implementation).

    Tries each secret in order: Ansari - Test, Ansari - Staging, Ansari (production).
    This is temporary until we determine which signature Meta sends per environment.

    Args:
        secrets_str: Comma-separated app secrets string
        body_bytes: Raw request body bytes
        received_signature: The signature received from the X-Hub-Signature-256 header

    Returns:
        bool: True if any secret verified successfully, False otherwise
    """
    app_secrets = [s.strip() for s in secrets_str.split(',')]
    app_names = ["Ansari - Test", "Ansari - Staging", "Ansari"]

    for i, secret in enumerate(app_secrets):
        if i >= len(app_names):
            continue  # Skip extra secrets beyond expected apps
        if _verify_signature_with_secret(secret, body_bytes, received_signature):
            logger.debug(f"Webhook signature verified successfully using {app_names[i]} app secret")
            return True
    return False


async def verify_meta_signature(request: Request) -> None:
    """
    Verify that the webhook request came from Meta using HMAC-SHA256 signature.

    Meta signs all webhook payloads with your app's App Secret and includes the signature
    in the X-Hub-Signature-256 header. This function validates that signature to ensure
    the request is authentic and hasn't been tampered with.

    References:
    - https://developers.facebook.com/docs/graph-api/webhooks/getting-started#validate-payloads
    - https://stackoverflow.com/questions/75422064/validate-x-hub-signature-256-meta-whatsapp-webhook-request

    Args:
        request: FastAPI Request object containing the webhook payload and headers

    Raises:
        HTTPException: 403 Forbidden if signature is invalid or missing

    Note:
        This is used with FastAPI's Depends() to automatically validate all
        webhook requests before processing them, similar to the authentication
        pattern used in ansari-backend.
    """
    # Get raw body bytes (cached after first read)
    body_bytes = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")

    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("Missing or invalid X-Hub-Signature-256 header format")
        logger.error("Webhook signature verification failed - rejecting request")
        raise HTTPException(
            status_code=403,
            detail="Invalid signature",
            headers={"WWW-Authenticate": "HMAC-SHA256"},
        )

    # Extract the signature from the header (remove "sha256=" prefix)
    signature_received_from_meta = signature_header.replace("sha256=", "")

    # TODO later (odyash): Implement single-secret verification when we know which secret Meta uses per env.
    # Try multi-secret verification (temporary implementation)
    if _verify_signature_multi(
        settings.META_ANSARI_APP_SECRET.get_secret_value(),
        body_bytes,
        signature_received_from_meta
    ):
        logger.debug("Webhook signature verified successfully")
        return

    # If no match happens, raise exception
    logger.error(
        "Invalid webhook signature; request isn't from Meta or you have misconfigured "
        "META_ANSARI_APP_SECRET"
    )
    raise HTTPException(
        status_code=403,
        detail="Invalid signature",
        headers={"WWW-Authenticate": "HMAC-SHA256"},
    )


def create_response_for_meta(
    success: bool = True,
    message: str = "OK",
    status_code: int = 200,
    error_code: str | None = None,
    details: dict | None = None
) -> Response:
    """
    Create appropriate webhook response based on deployment environment.

    In test environment: Returns proper HTTP status codes for testing
    In production/staging/local: Always returns 200 for Meta compliance

    Args:
        success: Whether the operation was successful
        message: Human-readable message
        status_code: HTTP status code to use (only in test mode)
        error_code: Machine-readable error code
        details: Additional details to include in response

    Returns:
        Response: HTTP response appropriate for current environment
    """
    # Create response body with structured information
    response_body = {
        "success": success,
        "message": message,
        "timestamp": int(__import__("time").time())
    }

    if error_code:
        response_body["error_code"] = error_code

    if details:
        response_body["details"] = details

    # When ALWAYS_RETURN_OK_TO_META is False: return proper HTTP status codes (for testing)
    # When ALWAYS_RETURN_OK_TO_META is True: always return 200 for Meta compliance
    if not settings.ALWAYS_RETURN_OK_TO_META:
        return JSONResponse(
            content=response_body,
            status_code=status_code if not success else 200
        )

    # Always return 200 for Meta compliance (production behavior)
    # But still include structured response body for logging/debugging
    return JSONResponse(
        content=response_body,
        status_code=200
    )


async def parse_meta_payload(
    body: dict[str, dict],
) -> tuple[bool, bool, str | None, str | None, dict | None, str | None, int | None]:
    """
    Parse the webhook payload received from Meta to extract relevant message details.

    Args:
        body (dict[str, dict]): The JSON body of the incoming webhook request from Meta.

    Returns:
        tuple: A tuple of (is_status, is_target_business_number, user_whatsapp_number,
               incoming_msg_type, incoming_msg_body, message_id, message_unix_time)

    Raises:
        Exception: If the payload structure is invalid or unsupported.
    """
    if not (
        body.get("object")
        and (entry := body.get("entry", []))
        and (changes := entry[0].get("changes", []))
        and (value := changes[0].get("value", {}))
    ):
        error_msg = f"Invalid received payload from WhatsApp user and/or problem with Meta's API:\n{body}"
        logger.error(error_msg)
        raise Exception(error_msg)

    # Check if this webhook is intended for our WhatsApp business number
    # Metadata should always be present in a valid webhook payload
    if "metadata" not in value:
        error_msg = f"Missing metadata in webhook payload from WhatsApp API:\n{value}"
        logger.error(error_msg)
        raise Exception(error_msg)

    if "phone_number_id" not in value["metadata"]:
        error_msg = f"Missing phone_number_id in webhook payload metadata:\n{value['metadata']}"
        logger.error(error_msg)
        raise Exception(error_msg)

    incoming_phone_number_id = value["metadata"]["phone_number_id"]
    configured_phone_number_id = settings.META_BUSINESS_PHONE_NUMBER_ID.get_secret_value()
    is_target_business_number = incoming_phone_number_id == configured_phone_number_id

    if not is_target_business_number:
        return None, is_target_business_number, None, None, None, None, None

    if "statuses" in value:
        # This is a status update (delivered, read, etc.), not a user message
        return True, is_target_business_number, None, None, None, None, None

    is_status = False

    if "messages" not in value:
        error_msg = f"Unsupported message type received from WhatsApp user:\n{body}"
        logger.error(error_msg)
        raise Exception(error_msg)

    incoming_msg = value["messages"][0]

    # Extract message details
    message_id = incoming_msg.get("id")
    user_whatsapp_number = incoming_msg["from"]
    message_unix_time_str = incoming_msg.get("timestamp")
    message_unix_time = int(message_unix_time_str) if message_unix_time_str is not None else None

    # Meta API note: Meta sends "errors" key when receiving unsupported message types
    # (e.g., video notes, gifs sent from giphy, or polls)
    incoming_msg_type = incoming_msg["type"] if incoming_msg["type"] in incoming_msg.keys() else "errors"
    incoming_msg_body = incoming_msg[incoming_msg_type]

    logger.info(f"Received a supported whatsapp message from {user_whatsapp_number}: {incoming_msg_body}")

    return (
        is_status,
        is_target_business_number,
        user_whatsapp_number,
        incoming_msg_type,
        incoming_msg_body,
        message_id,
        message_unix_time,
    )
