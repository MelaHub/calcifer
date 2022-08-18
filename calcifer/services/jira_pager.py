from typing import Optional
from calcifer.services.rest_pager import DEFAULT_PAGE_SIZE, QueryParams, RestPager


class JiraQueryParam(QueryParams):
    maxResults: int
    startAt: int
    jql: Optional[str]


class JiraPager(RestPager):

    total_param: Optional[str] = "total"

    def update_params(self, query_params: JiraQueryParam) -> JiraQueryParam:
        new_params = query_params.copy()
        new_params['startAt'] += self.page_size
        return new_params
