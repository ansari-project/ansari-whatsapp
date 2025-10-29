# General utility helpers for ansari-whatsapp
"""General utility functions that can be used across the codebase."""

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger


# Custom CORS middleware to log errors that occur in the middleware layer (if any)
class CORSMiddlewareWithLogging(CORSMiddleware):
    async def __call__(self, scope, receive, send):
        """Override the __call__ method to add logging"""
        if scope["type"] != "http":  # pragma: no cover
            return await super().__call__(scope, receive, send)

        # Create a Request object for logging
        request = Request(scope, receive)

        # Log detailed request information upfront to help debug CORS issues
        origin = request.headers.get("origin")
        host = request.headers.get("host")
        if "zrok" not in host:
            logger.debug(f"Incoming CORS Request: origin={origin}, host={host}")
        origin = origin if origin else host

        # Pre-check for CORS issues
        if origin and origin not in self.allow_origins and "*" not in self.allow_origins:
            logger.warning(f"CORS Origin mismatch detected: {origin} not in allowed origins: {self.allow_origins}")

        async def modified_send(message):
            """Intercept response to log CORS errors"""
            if message["type"] == "http.response.start":
                status = message["status"]
                # Common error details
                base_error = (
                    f"Status: {status}\n"
                    f"Path: {request.url.path}\n"
                    f"Method: {request.method}\n"
                    f"Origin: {origin}\n"
                    f"Host: {host}"
                )

                # Log CORS-related errors with more details
                if status >= 400:
                    if origin is not None and origin not in self.allow_origins:
                        logger.error(f"CORS Origin Error\n{base_error}\nAllowed: {self.allow_origins}")
                    elif request.method == "OPTIONS":
                        logger.error(f"CORS Preflight Error\n{base_error}")
                    else:
                        logger.error(f"HTTP Error Response\n{base_error}")
                elif status == 204 and request.method == "OPTIONS":
                    logger.debug(f"CORS Preflight Success\n{base_error}")

                # Log specific middleware errors
                if any(
                    [
                        status == 400 and request.method == "OPTIONS",
                        status == 401 and "Authorization" not in request.headers,
                        status == 403,
                        status == 429,
                    ]
                ):
                    logger.error(f"Middleware Error\n{base_error}")

            await send(message)

        # Monitor and log any exceptions from the CORS middleware
        try:
            await super().__call__(scope, receive, modified_send)
        except Exception as e:
            logger.error(
                (
                    f"Unhandled Middleware Error\nType: {type(e).__name__}\n"
                    f"Message: {str(e)}\n"
                    f"Path: {request.url.path}\n"
                    f"Method: {request.method}\n"
                    f"Origin: {origin}\n"
                    f"Host: {host}"
                ),
            )
