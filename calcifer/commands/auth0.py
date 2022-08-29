from calcifer.services.auth0_pager import (
    Auth0FromLogIdPager,
    Auth0LatestLogsPager,
    Auth0FromLogIdLogsParam,
    get_default_auth0_latest_logs_query_param,
)
from calcifer.utils.cache import cache_to_file
from typing import Optional

from calcifer.utils.json_logger import logger


@cache_to_file(file_prefix="auth0_latest_events")
def get_auth0_latest_events(
    auth0_pager: Auth0LatestLogsPager, auth0_search_str: Optional[str]
):
    logger.info("Getting latest 1000 events")

    params = get_default_auth0_latest_logs_query_param().copy()
    params["q"] = 'client_name%3D"Futuro User Platform"'

    return auth0_pager.get_all_pages(
        path="/logs", query_params=params, collection_name=None, show_progress=False
    )


@cache_to_file(file_prefix="auth0_after_log_id")
def get_auth0_events_after_log_id(
    auth0_pager: Auth0FromLogIdPager, from_log_id: str, auth0_search_str: Optional[str]
):

    logger.info(f"Getting events after {auth0_search_str}")
    params = Auth0FromLogIdLogsParam(take=100, q=auth0_search_str)
    params["from"] = from_log_id

    return auth0_pager.get_all_pages(
        path="/logs", query_params=params, collection_name=None, show_progress=False
    )


def flatten_logs(logs: list[dict]) -> list[dict]:
    for log in logs:
        error = log.get("details", {}).get("error", {})
        if type(error) == str:
            log.update(
                {"error_message": error, "error_oauth_error": "", "error_type": ""}
            )
        else:
            log.update(
                {
                    "error_message": log.get("details", {})
                    .get("error", {})
                    .get("message", ""),
                    "error_oauth_error": log.get("details", {})
                    .get("error", {})
                    .get("oauthError", ""),
                    "error_type": log.get("details", {})
                    .get("error", {})
                    .get("type", ""),
                }
            )
        for field in (
            "client_name",
            "user_name",
            "client_id",
            "user_id",
            "strategy",
            "connection",
            "strategy_type",
            "session_connection",
            "audience",
            "scope",
            "description",
            "auth0_client",
            "tracking_id",
        ):
            if field not in log:
                log[field] = ""
        if "details" in log:
            log.pop("details")
