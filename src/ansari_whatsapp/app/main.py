# Main WhatsApp API application
"""
FastAPI application for handling WhatsApp webhook requests.

This application serves as a wrapper around the Ansari backend API,
handling incoming webhook requests from the WhatsApp Business API
and forwarding them to the Ansari backend for processing.

NOTE: the `BackgroundTasks` logic is inspired by this issue and chat (respectively):
https://stackoverflow.com/questions/72894209/whatsapp-cloud-api-sending-old-message-inbound-notification-multiple-time-on-my
https://www.perplexity.ai/search/explain-fastapi-s-backgroundta-rnpU7D19QpSxp2ZOBzNUyg
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, Response, JSONResponse
from loguru import logger

from ansari_whatsapp.services.whatsapp_conversation_manager import WhatsAppConversationManager
from ansari_whatsapp.services.service_provider import get_ansari_client
from ansari_whatsapp.services.ansari_client_real import AnsariClientReal
from ansari_whatsapp.utils.whatsapp_webhook_utils import (
    parse_meta_payload,
    verify_meta_signature,
    create_response_for_meta,
)
from ansari_whatsapp.utils.time_utils import is_message_too_old
from ansari_whatsapp.utils.config import get_settings
from ansari_whatsapp.utils.general_helpers import CORSMiddlewareWithLogging
from ansari_whatsapp.utils.app_logger import configure_logger

# Configure logger at module load time
# This ensures logger is configured whether the app is run via:
# 1. Direct execution: python src/ansari_whatsapp/app/main.py
# 2. Uvicorn command: uvicorn src.ansari_whatsapp.app.main:app --reload
#
# Note: Configuring once is sufficient as loguru's logger is a global singleton.
# Any module that imports `from loguru import logger` will use the configured instance.
# See: https://github.com/Delgan/loguru/issues/54#issuecomment-461724397
configure_logger()


# Lifespan context manager for managing HTTP client lifecycle
# References:
# - https://fastapi.tiangolo.com/advanced/events/#lifespan
# - https://www.python-httpx.org/async/#opening-and-closing-clients
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifecycle of HTTP clients and other resources.

    This lifespan context manager ensures proper cleanup of resources like
    HTTP connection pools when the application starts and shuts down.

    Startup:
    - HTTP clients are created when first accessed via service provider

    Shutdown:
    - Close all HTTP clients to release connection pools
    - Clean up any background tasks or resources

    References:
    - https://fastapi.tiangolo.com/advanced/events/#lifespan
    - https://www.python-httpx.org/async/#opening-and-closing-clients
    """
    logger.info("Application startup: Initializing resources")
    # Store client instance for cleanup
    client = get_ansari_client()

    yield  # Application is running

    # Cleanup on shutdown
    logger.info("Application shutdown: Cleaning up resources")
    if isinstance(client, AnsariClientReal):
        await client.close()
        logger.info("HTTP client connections closed")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Ansari WhatsApp API",
    description="API for handling WhatsApp webhook requests for the Ansari service",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware with logging
app.add_middleware(
    CORSMiddlewareWithLogging,
    allow_origins=get_settings().ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"status": "ok", "message": "Ansari WhatsApp service is running"}


@app.get("/whatsapp/v2")
async def verification_webhook(request: Request) -> str | None:
    """
    Handles the WhatsApp webhook verification request.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        Optional[str]: The challenge string if verification is successful, otherwise raises an HTTPException.

    References:
        - https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests
    """
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.debug(f"Verification webhook received: {mode=}, {verify_token=}, {challenge=}")

    if mode and verify_token:
        if mode == "subscribe" and verify_token == get_settings().META_WEBHOOK_VERIFY_TOKEN.get_secret_value():
            logger.info("WHATSAPP WEBHOOK VERIFIED SUCCESSFULLY!")
            # Note: Challenge must be wrapped in an HTMLResponse for Meta to accept and verify the callback
            return HTMLResponse(challenge)
        logger.error("Verification failed: Invalid token or mode")
        raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Bad Request")


@app.post("/whatsapp/v2")
async def main_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(verify_meta_signature)
) -> Response:
    """
    Handles the incoming WhatsApp webhook message from Meta's WhatsApp Business API.

    This is the main webhook endpoint that processes all incoming messages from WhatsApp users.
    It performs several validation and filtering steps before processing user messages:

    **Processing Flow:**
    1. **Verify Signature**: Validates X-Hub-Signature-256 header to ensure request is from Meta
    2. **Extract Message Details**: Parses the webhook payload to extract relevant information
       (sender phone number, message type, message body, timestamps, etc.)
    
    3. **Validation Checks** (returns early if conditions met):
       - Verifies the webhook is for our WhatsApp business number
       - Filters out status messages (delivered, read, etc.)
       - Checks if service is under maintenance
       - Handles staging/local development routing (temporary workaround)
       - Validates message age (rejects messages older than configured threshold)
       - Verifies user registration status
       - Filters unsupported message types (non-text messages)
    
    4. **Background Processing**:
       - Starts typing indicator loop (shows user that bot is processing)
       - Processes text messages asynchronously via background tasks
    
    **Early Return Scenarios:**
    - Wrong business number: Returns 200 with skip message
    - Status message: Returns 200 with status acknowledgment
    - Maintenance mode: Sends maintenance message and returns 200
    - Staging filter: Returns 200 if message prefixed with "!d" in staging
    - Old message: Returns 200 after notifying user
    - Registration failure: Returns 500 error response
    - Unsupported media: Sends unsupported message and returns 200
    
    **Meta Webhook Compliance:**
    - Must respond quickly (within 20 seconds) to avoid retries
    - Returns 200 status code for successful receipt (actual processing happens in background)
    - All actual message processing is delegated to background tasks
    
    Args:
        request (Request): The incoming HTTP request containing the webhook payload from Meta.
        background_tasks (BackgroundTasks): FastAPI's background task manager for async processing.

    Returns:
        Response: HTTP response, typically with status code 200 to acknowledge receipt to Meta.
                 Response structure depends on ALWAYS_RETURN_OK_TO_META setting.
                 
    Raises:
        None: All exceptions are caught and handled, returning appropriate responses.
              Errors are logged but don't prevent Meta from receiving a 200 response.
    
    Note:
        - The function uses FastAPI's BackgroundTasks to process messages asynchronously,
          ensuring quick responses to Meta while handling potentially long-running operations.
        - The staging "!d" prefix filter is a temporary workaround until dedicated test numbers
          are available for each environment.
    """
    # Step 1: Signature verification now handled by Depends(verify_meta_signature_dependency)
    # Step 2: Parse the JSON payload
    data = await request.json()

    # Step 3: Extract message details from the webhook payload
    try:
        (
            is_status,
            is_target_business_number,
            from_whatsapp_number,
            incoming_msg_type,
            incoming_msg_body,
            message_id,
            message_unix_time,
        ) = await parse_meta_payload(data)

        # Check if this webhook is intended for our WhatsApp business phone number
        if not is_target_business_number:
            logger.debug("Ignoring webhook not intended for our WhatsApp business number")
            return create_response_for_meta(
                success=True,
                message="Skipping, as this webhook is not intended for our WhatsApp business number",
                status_code=200,
            )

        # Terminate if the incoming message is a status message (e.g., "delivered")
        if is_status:
            logger.debug("Ignoring status update message (e.g., delivered, read)")
            # This is a status message, not a user message, so doesn't need processing
            return create_response_for_meta(
                success=True,
                message="Status message processed (ignored)",
                error_code="STATUS_MESSAGE"
            )

        logger.debug(f"Incoming whatsapp webhook message from {from_whatsapp_number}")
    except Exception as e:
        logger.exception(f"Error extracting message details: {e}")
        return create_response_for_meta(
            success=False,
            message="Error processing webhook payload",
            status_code=400,
            error_code="INVALID_PAYLOAD",
            details={"error": str(e)}
        )

    # Create a user-specific conversation manager instance for this request
    conversation_manager = WhatsAppConversationManager(
        user_phone_num=from_whatsapp_number,
        incoming_msg_type=incoming_msg_type,
        incoming_msg_body=incoming_msg_body,
        message_id=message_id,
        message_unix_time=message_unix_time,
    )

    # Check if the WhatsApp service is enabled
    if get_settings().WHATSAPP_UNDER_MAINTENANCE:
        # Inform the user that the service is down for maintenance
        background_tasks.add_task(
            conversation_manager.send_whatsapp_message,
            "Ansari for WhatsApp is down for maintenance, please try again later or visit our website at https://ansari.chat.",
        )
        return create_response_for_meta(
            success=False,
            message="Service under maintenance",
            status_code=503,
            error_code="MAINTENANCE_MODE"
        )

    # Temporary corner case while locally developing:
    #   Since the staging server is always running,
    #   and since we currently have the same testing number for both staging and local testing,
    #   therefore we need an indicator that a message is meant for a dev who's testing locally now
    #   and not for the staging server.
    #   This is done by prefixing the message with "!d " (e.g., "!d what is ansari?")
    # NOTE: Obviously, this temp. solution will be removed when we get a dedicated testing number for staging testing.
    if get_settings().DEPLOYMENT_TYPE == "staging" and incoming_msg_body.get("body", "").startswith("!d "):
        logger.debug("Incoming message is meant for a dev who's testing locally now, so will not process it in staging...")
        return create_response_for_meta(
            success=False,
            message="Message filtered for local development",
            status_code=202,
            error_code="DEV_FILTER"
        )

    # Start the typing indicator loop that will continue until message is processed
    background_tasks.add_task(
        conversation_manager.send_typing_indicator_then_start_loop,
    )

    # Check if there are more than xx hours have passed from the user's message to the current time
    # If so, send a message to the user and return
    if is_message_too_old(message_unix_time):
        return create_response_for_meta(
            success=False,
            message="Message too old, notified user",
            status_code=422,
            error_code="MESSAGE_TOO_OLD"
        )

    # Check if the user's phone number is stored and register if not
    # Returns false if user's not found and their registration fails
    user_found: bool = await conversation_manager.check_and_register_user()
    if not user_found:
        background_tasks.add_task(
            conversation_manager.send_whatsapp_message, "Sorry, we couldn't register you to our database. Please try again later."
        )
        return create_response_for_meta(
            success=False,
            message="User registration failed",
            status_code=500,
            error_code="USER_REGISTRATION_FAILED"
        )

    # Check if the incoming message is a media type other than text
    if incoming_msg_type != "text":
        background_tasks.add_task(
            conversation_manager.handle_unsupported_message,
        )
        return create_response_for_meta(
            success=False,
            message="Unsupported message type handled",
            status_code=415,
            error_code="UNSUPPORTED_MESSAGE_TYPE"
        )

    # Process text messages sent by the WhatsApp user
    background_tasks.add_task(
        conversation_manager.handle_text_message,
    )

    return create_response_for_meta(
        success=True,
        message="Message processed successfully"
    )


if __name__ == "__main__":
    # This block is executed when the script is run directly
    # Alternative: Run with uvicorn command for auto-reload on .env file changes:
    #   uvicorn src.ansari_whatsapp.app.main:app --reload --reload-include .env
    import uvicorn
    import os

    settings = get_settings()

    # Determine module path for uvicorn dynamically
    #   (E.g.: ansari_whatsapp.app.main:app)
    file_path = os.path.abspath(__file__)
    module_path = os.path.relpath(file_path, os.getcwd())
    module_name = module_path.replace(os.sep, ".").replace(".py", "").replace("src.", "", 1) + ":app"
    logger.debug(f"Running FastAPI app with module name: {module_name}")

    if settings.DEPLOYMENT_TYPE == "local":
        host = "localhost"
        reload_uvicorn = True
        reload_includes = [".env"]
    else:
        host = "0.0.0.0"
        reload_uvicorn = False
        reload_includes = None

    # Run the FastAPI app with uvicorn
    uvicorn.run(
        module_name,  # Dynamically constructed module path
        host=host,
        port=8001,
        reload=reload_uvicorn,
        reload_includes=reload_includes,
        log_level=settings.LOGGING_LEVEL.lower(),
    )
