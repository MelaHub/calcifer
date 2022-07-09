from calcifer.services.rest_pager import RestPager

class JiraPager(RestPager):
    
    start_at_param: str = 'startAt',
    max_results_param: str = 'maxResults',
    total_param: str = 'total'