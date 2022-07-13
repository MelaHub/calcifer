from tokenize import String
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
    start_at_param: str
    max_results_param: str
    total_param: str

    def get_all_pages(self, path: str, query_params: dict, collection_name: str, map_item: Callable[dict, dict]=lambda item: item, show_progress: bool=True):
        
        def make_request(query_params: dict):
            import curlify
            print(f'{self.url}{path}')
            print(query_params)
            session = requests.Session()
            request = requests.Request('GET', f'{self.url}{path}', params=query_params, auth=HTTPBasicAuth(self.user, self.token.get_secret_value())).prepare()
            print(curlify.to_curl(request))
            response = session.send(request)
            if response.status_code in (404, 409):
                return []
            elif response.status_code != 200:
                raise Exception("Something went wrong while calling the github api")
            return response

        issues = []
        query_params.update({
            self.max_results_param: self.page_size,
            self.start_at_param: 0
        })

        # To refactor
        if self.total_param:
            response = make_request(query_params)
            curr_res = json.loads(response.content) # TODO: I'm actually making an extra call here
            for i in tqdm(range(0, curr_res[self.total_param], self.page_size), disable=not show_progress): # TODO: not sure if tdqm is just autocalculating the number of pages or what here
                response = make_request(query_params)
                curr_res = json.loads(response.content)
                if len(curr_res):
                    query_params[self.start_at_param] += self.page_size
                    if type(curr_res) is dict:
                        curr_res = curr_res[collection_name]
                    valid_results = [map_item(res) for res in curr_res.get(collection_name, curr_res)]
                    issues += valid_results
            return issues
        else:
            while True:
                response = make_request(query_params)
                curr_res = json.loads(response.content)
                print(f"{query_params} - {len(curr_res)}")
                if len(curr_res):
                    query_params[self.start_at_param] += self.page_size
                    if type(curr_res) is dict:
                        curr_res = curr_res[collection_name]
                    valid_results = [map_item(res) for res in curr_res]
                    issues += valid_results
                else:
                    break
            return issues
