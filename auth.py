# pytenable_was/auth.py

def build_headers(access_key: str, secret_key: str) -> dict:
    """
    Construct the required authentication headers for the Tenable WAS v2 API.

    Parameters:
        access_key (str): The Tenable Access Key.
        secret_key (str): The Tenable Secret Key.

    Returns:
        dict: A headers dictionary suitable for all WAS API requests.
    """
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-ApiKeys": f"accessKey={access_key}; secretKey={secret_key}",
    }
