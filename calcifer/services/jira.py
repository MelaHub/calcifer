from calcifer.services.rest_pager import RestPager

class JiraPager(RestPager):
    
    start_at_param: str = 'startAt',
    max_results_param: str = 'maxResults',
    total_param: str = 'total'

    def update_params(self, query_params: dict):
        if query_params:
            query_params[self.start_at_param] += self.page_size
        else:
         query_params.update({
            self.max_results_param: self.page_size,
            self.start_at_param: 0
        })