import time
import random
import asyncio
import requests
from requests_oauthlib import OAuth1
from fastapi import HTTPException
from functools import wraps
from app.config.settings import (
    NETSUITE_CONSUMER_KEY,
    NETSUITE_CONSUMER_SECRET,
    NETSUITE_TOKEN_ID,
    NETSUITE_TOKEN_SECRET,
    NETSUITE_ACCOUNT_ID
)
from app.config.logging_config import setup_logging

logger = setup_logging()

# Circuit breaker state
circuit_state = {
    "status": "closed",  # closed, open, half-open
    "failures": 0,
    "last_failure_time": 0,
    "threshold": 5,  # Number of failures before opening circuit
    "timeout": 60,  # Seconds to keep circuit open before trying again
}

def get_netsuite_auth():
    """
    Create OAuth1 authentication for NetSuite API requests.
    
    Returns:
        OAuth1 object configured for NetSuite authentication
    """
    return OAuth1(
        NETSUITE_CONSUMER_KEY,
        NETSUITE_CONSUMER_SECRET,
        NETSUITE_TOKEN_ID,
        NETSUITE_TOKEN_SECRET,
        signature_method="HMAC-SHA256",
        realm=NETSUITE_ACCOUNT_ID,
    )

def with_retry(max_retries=3, base_delay=1, max_delay=30):
    """
    Decorator to add exponential backoff retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    # Check circuit breaker before making the call
                    check_circuit_breaker()
                    
                    # Call the function
                    result = await func(*args, **kwargs)
                    
                    # On success, reset circuit breaker
                    reset_circuit_breaker()
                    return result
                    
                except HTTPException as e:
                    # Record failure in circuit breaker
                    record_failure()
                    
                    # Only retry on server errors (5xx)
                    if e.status_code < 500 or retries >= max_retries:
                        logger.error(f"Request failed after {retries} retries: {str(e)}")
                        raise
                        
                    # Calculate backoff with jitter
                    delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
                    logger.warning(f"Retry {retries+1}/{max_retries} after {delay:.2f}s: {str(e)}")
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
                    retries += 1
                    
                except Exception as e:
                    # Record failure in circuit breaker
                    record_failure()
                    
                    if retries >= max_retries:
                        logger.error(f"Request failed after {retries} retries: {str(e)}")
                        raise
                        
                    # Calculate backoff with jitter
                    delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
                    logger.warning(f"Retry {retries+1}/{max_retries} after {delay:.2f}s: {str(e)}")
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
                    retries += 1
        
        return wrapper
    return decorator

def check_circuit_breaker():
    """
    Check if the circuit breaker is open and should prevent API calls.
    
    Raises:
        HTTPException: If the circuit is open
    """
    if circuit_state["status"] == "open":
        # Check if enough time has passed to try again
        if time.time() - circuit_state["last_failure_time"] > circuit_state["timeout"]:
            # Move to half-open state to allow a test request
            circuit_state["status"] = "half-open"
            logger.info("Circuit breaker changed from open to half-open")
        else:
            # Circuit is still open, prevent the request
            logger.warning("Circuit breaker is open, preventing request to NetSuite API")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable: too many failed requests to NetSuite API"
            )

def record_failure():
    """Record a failed request in the circuit breaker state"""
    now = time.time()
    circuit_state["failures"] += 1
    circuit_state["last_failure_time"] = now
    
    if circuit_state["status"] == "half-open":
        # Immediately re-open circuit on failure in half-open state
        circuit_state["status"] = "open"
        logger.info("Circuit breaker changed from half-open to open after test request failure")
    elif circuit_state["status"] == "closed" and circuit_state["failures"] >= circuit_state["threshold"]:
        # Open circuit when failure threshold is reached
        circuit_state["status"] = "open"
        logger.info(f"Circuit breaker opened after {circuit_state['failures']} consecutive failures")

def reset_circuit_breaker():
    """Reset the circuit breaker after successful requests"""
    if circuit_state["status"] == "half-open":
        # Close circuit on success in half-open state
        circuit_state["status"] = "closed"
        circuit_state["failures"] = 0
        logger.info("Circuit breaker changed from half-open to closed after successful request")
    elif circuit_state["status"] == "closed":
        # Reset failure count on success
        circuit_state["failures"] = 0