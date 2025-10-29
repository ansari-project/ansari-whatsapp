# WhatsApp Webhook Parser
"""Utilities for parsing WhatsApp webhook payloads from Meta API."""

from loguru import logger

from ansari_whatsapp.utils.config import get_settings

settings = get_settings()


async def parse_webhook_payload(
    body: dict[str, dict],
) -> tuple[bool, bool, str | None, str | None, dict | None, str | None, int | None]:
    """
    Parse WhatsApp webhook payload to extract relevant message details.

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
