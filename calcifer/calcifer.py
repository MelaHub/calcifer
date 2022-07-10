import json
from turtle import pd
import requests
from requests.auth import HTTPBasicAuth
import click
import csv
from datetime import datetime
import itertools
from tqdm import tqdm
from os.path import exists
from calcifer.services.jira import JiraPager

from calcifer.services.github import get_all_repos, get_contributors_for_repo, get_commits_for_repo, get_commits_for_repo_with_tag, get_commit_with_sha

TAG_RELEASE = 'release-2021'


def print_iterator(it):
    for x in it:
        print(x, end=' ')
    print('') 

def get_top_contributors_for_repo(repo, github_user, github_token, n_contrib):
    content = get_contributors_for_repo(repo, github_user, github_token)
    return {
        'full_name': repo['full_name'],
        'total_commits': sum([x['contributions'] for x in content]),
        'contributors': [{'login': c['login'], 'contributions': c['contributions']} for c in content[0:n_contrib]]
    }

def write_main_contributors_to_file(contributors_repo, out_file_path):
    def get_key_by_index_or_empty(contributors, index, key):
        return contributors['contributors'][index][key] if len(contributors['contributors']) >= (index + 1) else ''

    contributors_by_repo = [{
        'full_name': r['full_name'],
        'total_commits': r['total_commits'],
        'contributor1': get_key_by_index_or_empty(r, 0, 'login'),
        'contributions1': get_key_by_index_or_empty(r, 0, 'contributions'),
        'contributor2': get_key_by_index_or_empty(r, 1, 'login'),
        'contributions2': get_key_by_index_or_empty(r, 1, 'contributions'),
        'contributor3': get_key_by_index_or_empty(r, 2, 'login'),
        'contributions3': get_key_by_index_or_empty(r, 2, 'contributions')}
         for r in contributors_repo]

    if not len(contributors_by_repo):
        print("No data found")
        return

    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=contributors_by_repo[0].keys())

        writer.writeheader()
        for contrib in contributors_by_repo:
            writer.writerow(contrib)

    print(f'I\'ve written {len(contributors_by_repo)} to {out_file_path}')
    

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--n-contrib", type=int, default=3)
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def main_contributors(github_user, github_token, github_org, out_file_path, n_contrib, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all contributors...')
    contributors_repo = map(lambda x: get_top_contributors_for_repo(x, github_user, github_token, n_contrib), tqdm(repos))
    write_main_contributors_to_file(contributors_repo, out_file_path)

def get_first_contribution_by_repo(repo, github_user, github_token):
    commits = get_commits_for_repo(repo, github_user, github_token)
    date_commits = [{'author': c['commit']['author']['name'], 'date': datetime.strptime(c['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ')} for c in commits]        
    return {
        author: {
            'date': min(commit['date'] for commit in commits),
            'repo': repo['name']
        }
        for author, commits in itertools.groupby(date_commits, lambda x: x['author'])}

def get_commits_with_tag(repo, github_user, github_token, tag):
    commits_with_tag = get_commits_for_repo_with_tag(repo, github_user, github_token, tag)
    commits_with_tag_details = []
    for commit in commits_with_tag:
        commit_details = get_commit_with_sha(repo, github_user, github_token, commit['commit']['sha'])
        commits_with_tag_details.append(
            {
                'repo': repo['name'],
                'tag': commit['name'],
                'author': commit_details['commit']['author']['name'],
                'message': commit_details['commit']['message'].replace('\n', '; '),
                'date': commit_details['commit']['author']['date']
            }
        )
    return commits_with_tag_details

def write_commits_on_file(commit_details, out_file_path):
    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=commit_details[0].keys())

        writer.writeheader()
        for commit in commit_details:
            writer.writerow(commit)

    print(f'I\'ve written {len(commit_details)} to {out_file_path}')

def write_first_contribution_to_file(first_contributions, out_file_path):
    def get_key_by_index_or_empty(contributors, index, key):
        return contributors['contributors'][index][key] if len(contributors['contributors']) >= (index + 1) else ''

    first_contributions_flat = [{
        'author': author,
        'date': first_contributions[author]['date'],
        'repo_name': first_contributions[author]['repo']}
         for author in first_contributions]

    if not len(first_contributions_flat):
        print("No data found")
        return

    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=first_contributions_flat[0].keys())

        writer.writeheader()
        for contrib in first_contributions_flat:
            writer.writerow(contrib)

    print(f'I\'ve written {len(first_contributions_flat)} to {out_file_path}')

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def first_contribution(github_user, github_token, github_org, out_file_path, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all contributors...')
    first_contributions = {}
    contributions_in_repo = map(lambda x: get_first_contribution_by_repo(x, github_user, github_token), tqdm(repos))
    for contribution in contributions_in_repo:
        for author in contribution:
            if first_contributions.setdefault(author, {'date': datetime.now(), 'repo': contribution[author]['repo']})['date'] > contribution[author]['date']:
                first_contributions[author] = contribution[author]
    write_first_contribution_to_file(first_contributions, out_file_path)

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def audit_releases(github_user, github_token, github_org, out_file_path, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all releases of this year...')
    commits = [c for c in map(lambda x: get_commits_with_tag(x, github_user, github_token, TAG_RELEASE), tqdm(repos))]
    write_commits_on_file([c for commits_per_repo in commits for c in commits_per_repo], out_file_path)


#TODO: parametrizzare progetto e created date
@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option("--jira-url", envvar="JIRA_URL", type=str, required=True, default='https://instapartners.atlassian.net')
@click.option("--search-for-user", type=str, required=True)
def issues_with_comments_by(jira_user, jira_api_token, jira_url, search_for_user):
    issues_cache = './issues_cache.json'
    if exists(issues_cache):
        with open(issues_cache, 'r') as f:
            issues = json.load(f)  
    else:
        issues = get_all_pages(
            f'{jira_url}/rest/api/3/search', 
            {'jql': 'project="Product support" AND createdDate > startOfYear()'}, 
            'issues',
            jira_user, 
            jira_api_token)
        with open(issues_cache, 'w') as f:
            json.dump(issues, f)

    comments_cache = './comments_by.json'
    if exists(comments_cache):
        with open(comments_cache, 'r') as f:
            issues_with_comments_by = json.load(f)  
    else:
        issues_with_comments_by = [comment for comment in map(
            lambda x: get_comments_by_issue(x, jira_url, jira_user, jira_api_token, search_for_user), tqdm(issues)) if comment]
        with open(comments_cache, 'w') as f:
            json.dump(issues_with_comments_by, f)

    with open('comments.csv', 'w') as f:
        f.write('issue,created\n')
        for issue in issues_with_comments_by:
            f.write(f'{issue[0]},{issue[1]}\n')

def get_comments_by_issue(issue, jira_url, jira_user, jira_api_token, search_for_user):
    comments = get_all_pages(
        f'{jira_url}/rest/api/3/issue/{issue["key"]}/comment', {}, 'comments', jira_user, jira_api_token)
    for comment in comments:
        if comment['author']['displayName'] == search_for_user:
            return [issue['key'], issue['fields']['created']]
    return None

@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option("--jira-url", envvar="JIRA_URL", type=str, required=True, default='https://instapartners.atlassian.net')
def issues_change_status_log(jira_user, jira_api_token, jira_url):
    jira_pager = JiraPager(
        user=jira_user, 
        token=jira_api_token, 
        url=jira_url)
    issues_cache = './issues_pfm_cache.json'
    if exists(issues_cache):
        with open(issues_cache, 'r') as f:
            issues = json.load(f)  
    else:
        issues = jira_pager.get_all_pages(
            f'/rest/api/3/search', 
            {'jql': 'project="Platform" AND createdDate > startOfYear()'}, 
            'issues')
        with open(issues_cache, 'w') as f:
            json.dump(issues, f)

    change_log_cache = './change_status_log'
    if exists(change_log_cache):
        with open(change_log_cache, 'r') as f:
            issues = json.load(f)  
    else:
        change_logs = []

        for i in tqdm(issues):
            change_log = jira_pager.get_all_pages(
                f'/rest/api/3/issue/{i["key"]}/changelog',
                {}, 
                'values',
                show_progress=False)
            for log in change_log:
                for field in log['items']:
                    if field['field'] == 'status':
                        assignee = i['fields']['assignee']['displayName'] if i['fields']['assignee'] else None
                        change_logs.append([i['key'], assignee, log['created'], field['fromString'], field['toString']])

        with open(change_log_cache, 'w') as f:
            json.dump(change_logs, f)
    

@click.group()
def cli():
    pass

cli.add_command(main_contributors)
cli.add_command(first_contribution)
cli.add_command(audit_releases)

cli.add_command(issues_with_comments_by)
cli.add_command(issues_change_status_log)
