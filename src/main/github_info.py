import requests
import os

BASE_URL = "https://api.github.com/repos/natherul/nath-bot/"


def setup():
    """Method to load  GitHub token from file if it is present"""
    if os.path.exists("git_token.txt"):
        t = open('git_token.txt', 'r')
        github_token = t.read()
        t.close()
        return github_token
    else:
        return ""


def get_data(type, git_token):
    """Method to get data from githubs API. Base path is the bot base path."""
    headers = {'Accept' : 'application/vnd.github+json',
               'X-GitHub-Api-Version' : '2022-11-28',
               'Authorization' : 'Bearer ' + git_token}
    response = requests.get(BASE_URL + type, headers=headers)
    return response.json()
