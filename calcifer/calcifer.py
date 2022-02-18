import json
import requests
from requests.auth import HTTPBasicAuth
import click
import csv
from tqdm import tqdm

def print_iterator(it):
    for x in it:
        print(x, end=' ')
    print('')  

def get_all_repos(github_org, github_user, github_token):
    print(f'Retrieving all {github_org} repos - hold on...')
    page_size = 100
    page = 0
    results = []
    while page is not None:
        response = requests.get(f'https://api.github.com/orgs/{github_org}/repos?per_page={page_size}&page={page}', auth = HTTPBasicAuth(github_user, github_token))
        if response.status_code != 200:
            raise Exception("Something went wrong while calling the github api")
        curr_res = json.loads(response.content)
        print(f'  retrieved {page * page_size + len(curr_res)} repos', end = '\r')
        if len(curr_res):
            page += 1
            results += curr_res
        else:
            page = None
    return results

def get_contributors_for_repo(repo, github_user, github_token, n_contrib):
    response = requests.get(repo['contributors_url'].replace('{/collaborator}', ''), auth = HTTPBasicAuth(github_user, github_token))
    content = []
    if response.status_code != 200 and response.status_code != 204:
        raise Exception(f"Something went wrong while fetching details of repo {repo}")
    elif response.status_code == 200:
        content = json.loads(response.content)[0:3]
    return {
        'full_name': repo['full_name'],
        'total_commits': sum([x['contributions'] for x in content]),
        'contributors': [{'login': c['login'], 'contributions': c['contributions']} for c in content[0:n_contrib]]
    }

def write_to_file(contributors_repo, out_file_path):
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
    contributors_repo = map(lambda x: get_contributors_for_repo(x, github_user, github_token, n_contrib), tqdm(repos))
    write_to_file(contributors_repo, out_file_path)

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
def first_contribution(github_user, github_token, github_org, out_file_path):
    print('Hi there')

@click.group()
def cli():
    pass

cli.add_command(main_contributors)
cli.add_command(first_contribution)
