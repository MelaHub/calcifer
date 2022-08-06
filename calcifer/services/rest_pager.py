from tokenize import String
from turtle import pd
import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
import math
import json
from pydantic import SecretStr, BaseModel, HttpUrl
from typing import Callable

REPO_PAGE_SIZE = 100

class RestPager(BaseModel):

    user: str
    token: SecretStr
    url: HttpUrl
    page_size: int = REPO_PAGE_SIZE
    total_param: int = None

    def update_params(self, query_params: dict) -> None:
        raise NotImplementedError

    def get_all_pages(self, path: str, query_params: dict, collection_name: str, map_item: Callable[dict, dict]=lambda item: item, show_progress: bool=True) -> list:
        
        if self.url in path:
            path = path.replace(self.url, '')

        def make_request(query_params: dict):
            session = requests.Session()
            request = requests.Request('GET', f'{self.url}{path}', params=query_params, auth=HTTPBasicAuth(self.user, self.token.get_secret_value())).prepare()
            response = session.send(request)
            if response.status_code in (404, 409):
                return []
            elif response.status_code != 200:
                raise Exception("Something went wrong while calling the github api")
            return response

        issues = []
        self.update_params(query_params)

        # TODO: refactor the two branches
        if self.total_param:
            response = make_request(query_params)
            curr_res = json.loads(response.content) # TODO: I'm actually making an extra call here
            for i in tqdm(range(0, curr_res[self.total_param], self.page_size), disable=not show_progress): # TODO: not sure if tdqm is just autocalculating the number of pages or what here
                response = make_request(query_params)
                curr_res = json.loads(response.content)
                if len(curr_res):
                    self.update_params(query_params)
                    if type(curr_res) is dict:
                        curr_res = curr_res[collection_name]
                    valid_results = [map_item(res) for res in curr_res]
                    issues += valid_results
            return issues
        else:
            while True: # TODO: this is for github that doesn't give the total number of repos; only way to do it is to use graphql https://docs.github.com/en/graphql
                response = make_request(query_params)
                curr_res = json.loads(response.content)
                if type(curr_res) is dict:
                    if collection_name:
                        curr_res = curr_res.get(collection_name, [])
                    else:
                        issues += [map_item(res) for res in [curr_res]] # This is a response with a single result
                        break
                if len(curr_res):
                    self.update_params(query_params)
                    valid_results = [map_item(res) for res in curr_res]
                    issues += valid_results
                else:
                    break
            return issues
