from tokenize import String
import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
import math
import json
from pydantic import SecretStr, BaseModel

REPO_PAGE_SIZE = 100

# TODO Nota che questo è in realtà solo valido per jira
class RestPager(BaseModel):

    user: str
    token: SecretStr
    url: str # TODO(maybe there's a type for uri?)

    def get_all_pages(self, path, query_params, collection_name, map_item=lambda item: item, show_progress=True):
        def make_request(query_params):
            response = requests.get(f'{self.url}{path}', params = query_params, auth = HTTPBasicAuth(self.user, self.token.get_secret_value()))
            if response.status_code in (404, 409):
                return []
            elif response.status_code != 200:
                raise Exception("Something went wrong while calling the github api")
            return response

        page_size = REPO_PAGE_SIZE
        issues = []
        query_params.update({
            'maxResults': page_size,
            'startAt': 0
        })
        response = make_request(query_params)
        page_number = math.ceil(response.json()['total'] / page_size)
        for i in tqdm(range(page_number), disable=not show_progress):
            response = make_request(query_params)
            curr_res = json.loads(response.content)
            if len(curr_res):
                query_params['startAt'] += page_size
                valid_results = [map_item(res) for res in curr_res[collection_name]]
                issues += valid_results
        return issues
