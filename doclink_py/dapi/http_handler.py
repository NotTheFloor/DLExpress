import requests
import json
import logging

DEFAULT_AUTH_CODE: str = "none_yet"
CLOUD_PREFIX: str = "CloudAPI/"
ON_PREM_PREFIX: str = "DocLinkAPI/"


class HTTPHandler:
    """Class to handle HTTP requests, seperating business logic"""

    def __init__(self, base_url: str) -> None:
        """Initialize the HTTPHandler class."""
        self.base_url = base_url
        self.auth_code = DEFAULT_AUTH_CODE
        self.header: dict[str, str] = {
            "AuthCode": self.auth_code,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.authenticated: bool = False

        self.prefix: str = CLOUD_PREFIX

    def set_mode_on_prem(self) -> None:
        """Set the prefix for the URL."""
        logging.debug(f"Setting prefix to {ON_PREM_PREFIX}")
        self.prefix = ON_PREM_PREFIX

    def logged_in(self, response: str) -> None:
        """Update the authentication code after successful login."""
        self.update_auth_code(response)
        self.authenticated = True

    def logged_out(self) -> None:
        """Reset the authentication code after successful logout."""
        self.update_auth_code(DEFAULT_AUTH_CODE)
        self.authenticated = False

    def update_auth_code(self, auth_code: str) -> None:
        """Update the authentication code."""
        self.auth_code = auth_code
        self.header["AuthCode"] = auth_code

    def get_request(
        self,
        url: str,
        parameters: dict | None = {},
        requires_auth: bool | None = True,
    ) -> dict | list:
        """Send a GET request to the specified URL."""
        logging.debug(f"Sending GET request to {url} with parameters {parameters}")
        self._check_authenticated(requires_auth)

        response: requests.Response = requests.get(
            self.base_url + self.prefix + url,
            headers=self.header,
            params=parameters,
        )
        response.raise_for_status()
        logging.debug(f"Response: {json.dumps(response.json(), indent=4)}")

        return response.json()

    def post_request(
        self, url: str, data: dict, requires_auth: bool | None = True
    ) -> dict | list:
        """Send a POST request to the specified URL."""
        logging.debug(
            f"Sending POST request to {url} with data {json.dumps(data, indent=4)}"
        )
        self._check_authenticated(requires_auth)

        response: requests.Response = requests.post(
            self.base_url + self.prefix + url,
            headers=self.header,
            data=json.dumps(data),
        )
        response.raise_for_status()

        if not response.content:
            return {}
        logging.debug(f"Response: {json.dumps(response.json(), indent=4)}")

        return response.json()

    def _check_authenticated(self, requires_auth: bool) -> None:
        """Private method to check if the user is authenticated."""
        if requires_auth and not self.authenticated:
            raise Exception("NOT_AUTHENTICATED", "User is not authenticated")
