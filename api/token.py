# OBSOLETE MODULE, but saving just in case

from datetime import datetime, timedelta
from typing import Dict

class Token:
    VALID_TIME_PERIOD = timedelta(hours=3)
    def __init__(self, token):
        self._token = token
        self._issue_time = datetime.now()
        self._last_used = self._issue_time
        self._expiration_time = self.issue_time + Token.VALID_TIME_PERIOD

    def is_expired(self) -> bool:
        return datetime.now() > self._expiration_time # Current time is past the expiration time

    def renew_token(self):
        self._expiration_time = datetime.now() + Token.VALID_TIME_PERIOD

    def update_used(self): #Returns itself for easy chaining
        self._last_used = datetime.now()
        return self

class TokenHolder:
    def __init__(self):
        self._tokens: Dict[int, Token] = {}
        self._token_counter = 0

    def issue_token(self) -> Token:
        self._token_counter += 1
        token = Token(self._token_counter)
        self._tokens[self._token_counter] = token
        return token

    def is_valid_token(self, token: int) -> bool:
        return token in self._tokens and not self._tokens[token].is_expired()

    def get_token(self, token: int) -> Token:
        if self.is_valid_token(token):
            return self._tokens[token].update_used()
    
    