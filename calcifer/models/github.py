from typing import TypedDict
from pydantic import HttpUrl


class RepoOwner(TypedDict):
    login: str


class RequiredStatusCheck(TypedDict):
    strict: bool


class RequiredPullRequestReviews(TypedDict):
    required_approving_review_count: int
    dismiss_stale_reviews: bool


class AllowForcePushes(TypedDict):
    enabled: bool


class RequireLinearHistory(TypedDict):
    enabled: bool


class Repo(TypedDict):
    name: str
    full_name: str
    private: bool
    archived: bool
    default_branch: str
    git_tags_url: HttpUrl
    commits_url: HttpUrl
    visibility: bool
    owner: RepoOwner


class RepoProtection(TypedDict):
    required_status_checks: RequiredStatusCheck
    required_pull_request_reviews: RequiredPullRequestReviews
    allow_force_pushes: AllowForcePushes
    require_linear_history: RequireLinearHistory
    url: HttpUrl


class RepoProtectionInfo(TypedDict):
    name: str
    visibility: bool
    required_status_checks: bool
    dismiss_stale_review: bool
    require_approving_review_count: int
    allow_force_pushes: bool
    require_linear_history: bool
    is_protection_missing: bool


class FlattenCommit(TypedDict):
    repo: str
    tag: str
    author: str
    message: str
    date: str


class Commit(TypedDict):
    sha: str
    url: HttpUrl


class Tag(TypedDict):
    name: str
    commit: Commit


class Author(TypedDict):
    name: str
    date: str


class CommitDetails(TypedDict):
    author: Author
    message: str


class CommitDetails(TypedDict):
    name: str
    commit: CommitDetails


class AuthorContribution(TypedDict):
    author: str
    date: str
    repo: str


class RepoCommits(TypedDict):
    name: str
    commits: int


class Contributor(TypedDict):
    login: str


class ContributorWithRepo(TypedDict):
    login: str
    repo: str
