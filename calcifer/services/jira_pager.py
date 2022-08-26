from typing import Optional
from calcifer.services.rest_pager import DEFAULT_PAGE_SIZE, QueryParams, RestPager
from pydantic import SecretStr, HttpUrl
from requests.auth import HTTPBasicAuth


class JiraQueryParam(QueryParams):
    maxResults: int
    startAt: int
    jql: Optional[str]


def get_default_query_param() -> JiraQueryParam:
    return JiraQueryParam(maxResults=DEFAULT_PAGE_SIZE, startAt=0)


class JiraPager(RestPager):

    def __init__(self, url: HttpUrl, user: str, token: SecretStr) -> None:
        self.url = url
        self.total_param = "total"
        self.auth = HTTPBasicAuth(user, token.get_secret_value())

    def update_params(self, query_params: JiraQueryParam, last_results: list[dict]) -> JiraQueryParam:
        new_params = query_params.copy()
        new_params["startAt"] += self.page_size
        return new_params
