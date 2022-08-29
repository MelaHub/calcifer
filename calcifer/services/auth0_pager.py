from typing import Optional
from calcifer.services.rest_pager import (
    DEFAULT_PAGE_SIZE,
    QueryParams,
    RestPager,
    HTTPBearer,
)
from pydantic import SecretStr, HttpUrl


class Auth0LatestLogsParam(QueryParams):
    page: int
    per_page: int
    q: Optional[str]


# Note: not using an explicit "from" here because it's a reserved word
# However, to make this work you should also append a 'from' key
class Auth0FromLogIdLogsParam(QueryParams):
    take: int
    q: Optional[str]


def get_default_auth0_latest_logs_query_param() -> Auth0LatestLogsParam:
    return Auth0LatestLogsParam(page=0, per_page=DEFAULT_PAGE_SIZE, q=None)


class Auth0FromLogIdPager(RestPager[Auth0FromLogIdLogsParam]):
    def __init__(self, url: HttpUrl, bearer: SecretStr) -> None:
        self.url = url
        self.auth = HTTPBearer(bearer.get_secret_value())

    def update_params(
        self, query_params: Auth0FromLogIdLogsParam, last_results: list[dict]
    ) -> Auth0FromLogIdLogsParam:
        new_params = query_params.copy()
        new_params["from"] = last_results[-1]["log_id"]
        return new_params


class Auth0LatestLogsPager(RestPager[Auth0LatestLogsParam]):
    def __init__(self, url: HttpUrl, bearer: SecretStr) -> None:
        self.url = url
        self.auth = HTTPBearer(bearer.get_secret_value())

    def update_params(
        self, query_params: Auth0LatestLogsParam, last_results: list[dict]
    ) -> Auth0LatestLogsParam:
        new_params = query_params.copy()
        new_params["page"] += 1
        return new_params
