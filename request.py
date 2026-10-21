from dataclasses import dataclass


@dataclass
class Request:
    method: str
    path: str
    headers: dict
    body: str
    query: dict = None
    cookies: dict = None
    params: dict = None

    def __post_init__(self):
        if self.query is None:
            self.query = {}
        if self.cookies is None:
            self.cookies = {}
        if self.params is None:
            self.params = {}
