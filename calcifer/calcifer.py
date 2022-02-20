import json
import requests
from requests.auth import HTTPBasicAuth
import click
import csv
from datetime import datetime
import itertools
from tqdm import tqdm

REPO_PAGE_SIZE = 100

def print_iterator(it):
    for x in it:
        print(x, end=' ')
    print('') 

def get_all_pages(url, query_params, github_user, github_token, stop_if=lambda x: False, page_size=REPO_PAGE_SIZE, max_results=None):
    page_size = page_size if max_results is None or max_results > page_size else max_results
    results = []
    query_params.update({
        'per_page': page_size,
        'page': 0
    })
    while query_params['page'] is not None and (max_results is None or max_results is not None and len(results) < max_results):
        query_params_str = '&'.join([f'{k}={query_params[k]}' for k in query_params])
        response = requests.get(f'{url}?{query_params_str}', auth = HTTPBasicAuth(github_user, github_token))
        if response.status_code not in (200, 404, 409):
            return []
            raise Exception("Something went wrong while calling the github api")
        if response.status_code in (404, 409):
            return []
        curr_res = json.loads(response.content)
        if len(curr_res):
            query_params['page'] += 1
            valid_results = [res for res in curr_res if not stop_if(res)]
            results += valid_results
            if len(valid_results) < len(curr_res):
                break
        else:
            query_params['page'] = None
    return results

def get_all_repos(github_org, github_user, github_token):
    print(f'Retrieving all {github_org} repos - hold on...')
    return get_all_pages(f'https://api.github.com/orgs/{github_org}/repos', {}, github_user, github_token)

def get_contributors_for_repo(repo, github_user, github_token):
    response = requests.get(repo['contributors_url'].replace('{/collaborator}', ''), auth = HTTPBasicAuth(github_user, github_token))
    content = []
    if response.status_code != 200 and response.status_code != 204:
        raise Exception(f"Something went wrong while fetching details of repo {repo}")
    elif response.status_code == 200:
        content = json.loads(response.content)
    return content

def get_top_contributors_for_repo(repo, github_user, github_token, n_contrib):
    content = get_contributors_for_repo(repo, github_user, github_token)
    return {
        'full_name': repo['full_name'],
        'total_commits': sum([x['contributions'] for x in content]),
        'contributors': [{'login': c['login'], 'contributions': c['contributions']} for c in content[0:n_contrib]]
    }

def get_commits_for_repo(repo, github_user, github_token):
    stop_if = lambda x: datetime.strptime(x['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ') < datetime(2016, 1, 1)
    main_response = get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'main'}, github_user, github_token, stop_if=stop_if)
    master_response = get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'master'}, github_user, github_token, stop_if = stop_if)
    return main_response + master_response

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
def main_contributors(github_user, github_token, github_org, out_file_path, n_contrib):
    repos = get_all_repos(github_org, github_user, github_token)
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
def first_contribution(github_user, github_token, github_org, out_file_path):
    repos = get_all_repos(github_org, github_user, github_token)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all contributors...')
    first_contributions = {}
    contributions_in_repo = map(lambda x: get_first_contribution_by_repo(x, github_user, github_token), tqdm(repos))
    for contribution in contributions_in_repo:
        for author in contribution:
            if first_contributions.setdefault(author, {'date': datetime.now(), 'repo': contribution[author]['repo']})['date'] > contribution[author]['date']:
                first_contributions[author] = contribution[author]
    write_first_contribution_to_file(first_contributions, out_file_path)

@click.group()
def cli():
    pass

cli.add_command(main_contributors)
cli.add_command(first_contribution)
