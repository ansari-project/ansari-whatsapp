# WhatsApp Logger for ansari-whatsapp
"""Logging configuration for the WhatsApp service using Loguru."""

import json
import os
import sys

from loguru import logger

from ansari_whatsapp.utils.config import get_settings

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Track if logger has been configured globally to avoid duplicate handlers
_logger_configured = False

logger.remove()  # Remove default handler to prevent duplicate logs

def configure_logger():
    """Configure the global logger with handlers for console and file output.

    This should be called once at application startup (in main.py's if __name__ == "__main__" block).
    After configuration, use `from loguru import logger` directly in other modules.
    """
    global _logger_configured

    # Only configure handlers once globally
    if _logger_configured:
        return

    _logger_configured = True

    # Get settings
    settings = get_settings()

    # Determine if we should use JSON structured logging for AWS CloudWatch
    # CloudWatch Logs Insights works best with JSON-formatted logs
    is_aws_deployment = settings.DEPLOYMENT_TYPE not in ["local", "development"]

    # Filter for test files only (when LOG_TEST_FILES_ONLY is True)
    def log_filter(record):
        """Filter logs based on test file settings.

        Args:
            record: The log record being processed.
        """
        # If LOG_TEST_FILES_ONLY is True, only allow logs from files in "tests" folder or files starting with "test_"
        if settings.LOG_TEST_FILES_ONLY and not (
            "tests" in record["file"].path or "test_" in record["file"].name
        ):
            return False

        return True

    # Choose format and serialization based on deployment type
    if is_aws_deployment:
        # JSON format for AWS CloudWatch (structured logging)
        # Using Loguru's built-in serialize=True feature
        # This automatically converts log records to JSON with all fields
        #
        # Important: json.dumps() automatically escapes newlines as \n in the JSON string
        # This ensures multi-line messages (like CORS errors with \n) are kept as
        # a SINGLE log entry in CloudWatch, which expands when clicked in the console
        #
        # Example output for multi-line message:
        # {"text": "CORS Error\nStatus: 403\nPath: /api", "record": {...}}
        # In CloudWatch, this appears as ONE entry that expands to show all lines
        use_serialize = True
        enable_colors = False
    else:
        # Colorized format for local development
        use_serialize = False
        enable_colors = True

    # Add console handler for terminal output
    logger.add(
        sys.stderr,
        format="{message}" if is_aws_deployment else (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <4}</level> | "
            "<cyan>{file}</cyan>:<cyan>{line}</cyan> "
            "<blue>[{function}()]</blue> | "
            "<level>{message}</level>"
        ),
        level=settings.LOGGING_LEVEL.upper(),
        enqueue=True,
        colorize=enable_colors,
        backtrace=False,
        diagnose=False,
        filter=log_filter,
        catch=False,
        serialize=use_serialize,  # Enable JSON serialization for AWS
    )

    # Write logs to all_logs.log file (IF we're running locally)
    if settings.DEPLOYMENT_TYPE == "local":
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        all_logs_file = os.path.join(log_dir, "all_logs.log")
        logger.add(
            all_logs_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file}:{line} [{function}()] | {message}",
            level=settings.LOGGING_LEVEL.upper(),
            enqueue=True,
            backtrace=False,
            diagnose=False,
            filter=log_filter,
            rotation="10 MB",
            catch=False,
        )