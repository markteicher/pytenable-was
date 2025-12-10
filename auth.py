# pytenable_was/auth.py

"""
Authentication utilities for the Tenable WAS v2 API.

This module is intentionally small but full-featured:
- Validates that credentials are present
- Builds the correct X-ApiKeys header
- Allows caller-specified extra headers (e.g., custom User-Agent)
- Supports loading credentials from environment variables
- Logs auth setup without ever logging raw secrets
"""

import logging
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _mask_key(value: str, visible: int = 4) -> str:
    """
    Mask a key for safe logging.

    Example:
        ABCDEFGH -> ****EFGH
    """
    if not value:
        return ""
    value = str(value)
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def build_headers(
    access_key: str,
    secret_key: str,
    extra_headers: Optional[Dict[str, str]] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, str]:
    """
    Construct the required authentication headers for the Tenable WAS v2 API.

    Parameters:
        access_key (str): The Tenable Access Key.
        secret_key (str): The Tenable Secret Key.
        extra_headers (dict, optional):
            Additional headers to merge into the base auth headers.
        user_agent (str, optional):
            Custom User-Agent value to advertise the client.

    Returns:
        dict: A headers dictionary suitable for all WAS API requests.
    """
    if not access_key or not secret_key:
        logger.error("Access key or secret key missing when building headers.")
        raise ValueError("Both access_key and secret_key are required.")

    masked_access = _mask_key(access_key)
    masked_secret = _mask_key(secret_key)
    logger.debug(
        "Building WAS auth headers with access_key=%s, secret_key=%s",
        masked_access,
        masked_secret,
    )

    headers: Dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ApiKeys": f"accessKey={access_key}; secretKey={secret_key}",
    }

    if user_agent:
        headers["User-Agent"] = user_agent
        logger.debug("Custom User-Agent set: %s", user_agent)

    if extra_headers:
        headers.update(extra_headers)
        logger.debug("Extra headers merged into auth headers: %s", list(extra_headers.keys()))

    return headers


def load_credentials_from_env(
    access_var: str = "TENABLE_ACCESS_KEY",
    secret_var: str = "TENABLE_SECRET_KEY",
) -> Tuple[str, str]:
    """
    Load Tenable credentials from environment variables.

    Parameters:
        access_var (str): Env var name for the access key.
        secret_var (str): Env var name for the secret key.

    Returns:
        (access_key, secret_key) tuple.

    Raises:
        ValueError: If either variable is not set.
    """
    access_key = os.getenv(access_var)
    secret_key = os.getenv(secret_var)

    if not access_key or not secret_key:
        logger.error(
            "Environment credentials missing. Expected %s and %s.",
            access_var,
            secret_var,
        )
        raise ValueError(
            f"Environment variables {access_var} and {secret_var} must be set."
        )

    logger.info(
        "Loaded Tenable credentials from environment (%s, %s).",
        access_var,
        secret_var,
    )

    return access_key, secret_key
