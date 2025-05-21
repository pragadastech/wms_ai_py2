import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.logging_config import setup_logging

logger = setup_logging()

class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch all unhandled exceptions in the application.
    Logs exceptions and returns standardized error responses to clients.
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = f"{time.time()}-{request.client.host}"
        request.state.request_id = request_id
        
        # Add request info to all log messages
        logger_ctx = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host
        }
        
        try:
            # Attempt to process the request normally
            logger.info(f"Request started: {request.method} {request.url.path}", extra=logger_ctx)
            start_time = time.time()
            
            response = await call_next(request)
            
            # Log successful request completion
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s",
                extra=logger_ctx
            )
            return response
            
        except Exception as e:
            # Log the exception with traceback
            process_time = time.time() - start_time
            logger.exception(
                f"Unhandled exception: {request.method} {request.url.path} - {str(e)} - Time: {process_time:.3f}s",
                extra=logger_ctx
            )
            
            # Return standardized error response to client
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "An internal server error occurred",
                    "request_id": request_id,  # Include for error tracking
                    "detail": str(e) if isinstance(e, Exception) else "Unknown error"
                }
            ) 