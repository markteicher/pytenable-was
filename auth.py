# pytenable_was/auth.py

import logging

logger = logging.getLogger(__name__)

def build_headers(access_key: str, secret_key: str, extra_headers: dict = None) -> dict:
    """
    Construct the required authentication headers for the Tenable WAS v2 API.
    Adds logging, input validation, and optional custom headers.

    Parameters:
        access_key (str): The Tenable Access Key.
        secret_key (str): The Tenable Secret Key.
        extra_headers (dict, optional): Additional headers to merge.

    Returns:
        dict: A headers dictionary suitable for all WAS API requests.
    """

    # Validate keys
    if not access_key or not secret_key:
        logger.error("Access Key or Secret Key missing.")
        raise ValueError("Both access_key and secret_key are required.")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ApiKeys": f"accessKey={access_key}; secretKey={secret_key}",
    }

    # Merge optional headers, if provided
    if extra_headers:
        headers.update(extra_headers)
        logger.debug(f"Extra headers merged: {extra_headers}")

    logger.debug("Authentication headers successfully created.")
    return headers
