from turtle import pd
import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
import json
from pydantic import SecretStr, BaseModel, HttpUrl
from typing import Callable, TypedDict, Generic,  TypeVar
from calcifer.utils.json_logger import logger

DEFAULT_PAGE_SIZE = 100

class NoResponse(Exception):
    pass


class QueryParams(TypedDict):
    pass


T = TypeVar('T', bound=QueryParams)


class RestPager(BaseModel, Generic[T]):

    user: str
    token: SecretStr
    url: HttpUrl
    page_size: int = DEFAULT_PAGE_SIZE
    total_param: Optional[str] = None

    def update_params(self, query_params: T) -> T:
        raise NotImplementedError

    def get_all_pages(
        self,
        path: str,
        query_params: T,
        collection_name: str,
        map_item: Callable[dict, dict] = lambda item: item,
        show_progress: bool = True,
        stop_if: Callable[dict, bool] = None,
    ) -> list:

        if stop_if is None:
            stop_if = lambda x: False

        if self.url in path:
            path = path.replace(self.url, "")

        def make_request(query_params: T):
            response = requests.get(
                f"{self.url}{path}",
                params=query_params,
                auth=HTTPBasicAuth(self.user, self.token.get_secret_value()),
            )
            if response.status_code in (404, 409, 204):
                return []
            elif response.status_code == 200:
                return json.loads(response.content)
            else:
                logger.error(
                    f"Failed call {response.request.method}/{response.request.url} {response.request.body} "
                    f"with response {response.status_code} {response.content}"
                )
                raise Exception("Something went wrong while calling the github api")

        data = []

        # TODO: refactor the two branches
        if self.total_param:
            curr_res = make_request(
                query_params
            )  # TODO: I'm actually making an extra call here
            for i in tqdm(
                range(0, curr_res[self.total_param], self.page_size),
                disable=not show_progress,
            ):  # TODO: not sure if tdqm is just autocalculating the number of pages or what here
                curr_res = make_request(query_params)
                if len(curr_res):
                    query_params = self.update_params(query_params)
                    if type(curr_res) is dict:
                        curr_res = curr_res[collection_name]
                    if stop_if(curr_res[0]):
                        break
                    valid_results = [map_item(res) for res in curr_res]
                    data += valid_results
            return data
        else:
            while (
                True
            ):  # TODO: this is for github that doesn't give the total number of repos; only way to do it is to use graphql https://docs.github.com/en/graphql
                curr_res = make_request(query_params)
                if type(curr_res) is dict:
                    if collection_name:
                        curr_res = curr_res.get(collection_name, [])
                    else:
                        data += [
                            map_item(res) for res in [curr_res]
                        ]  # This is a response with a single result
                        break
                if len(curr_res):
                    if stop_if(curr_res[0]):
                        break
                    query_params = self.update_params(query_params)
                    valid_results = [map_item(res) for res in curr_res]
                    data += valid_results
                else:
                    break
            return data
