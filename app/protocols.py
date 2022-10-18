from typing import Protocol, Optional


class Authenticator(Protocol):
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """An authenticator can authenticate"""
