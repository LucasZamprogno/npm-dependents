from bs4 import BeautifulSoup
import requests

TOKEN = "GITHUB ACCESS TOKEN HERE"

def get(url):
    return requests.get(url).text

# Getting github link from https://www.npmjs.com/package/chai
def get_github_from_npm_link(url):
    soup = BeautifulSoup(get(url), 'html.parser')
    return find_github_url(soup)

def find_github_url(soup):
    github_section = soup.find(match_repository_link)
    if github_section is None:
        return None
    return github_section.find_next_sibling().find('a')['href']

def match_repository_link(soup):
    return soup.name == "h3" and soup.get_text() == "Repository"

# Getting links from https://www.npmjs.com/browse/depended/chai
def get_dependent_links_from_url(url):
    soup = BeautifulSoup(get(url), 'html.parser')
    return find_all_dependents_on_page(soup)

def find_all_dependents_on_page(soup):
    sections = soup.find_all('section')
    a_elems = [section.find(match_npm_link_from_dependents) for section in sections]
    return ["https://www.npmjs.com/" + elem['href'] for elem in a_elems]

def match_npm_link_from_dependents(soup):
    return soup.name == 'a' and soup.find('h3') is not None

# Getting stars from https://github.com/chaijs/chai
def get_stars_from_url(url):
    new_url = url.replace("https://github.com", "https://api.github.com/repos")
    response = requests.get(new_url, headers={'Authorization': 'access_token %s' % TOKEN})
    if response.status_code != 200: # Most likely link from npm 404'd
        return None
    return response.json()["stargazers_count"]

def get_github_and_stars_from_dependents_page(url):
    links = get_dependent_links_from_url(url)

    repos = []
    for link in links:
        repo = get_github_from_npm_link(link)
        if repo is not None:
            print("Adding repo ", repo)
            repos.append(repo)
            break

    pairs = []
    for repo in repos:
        stars = get_stars_from_url(repo)
        if stars is not None:
            print("Adding pair ", (repo, stars))
            pairs.append((repo, stars))

    return pairs

print(get_github_and_stars_from_dependents_page("https://www.npmjs.com/browse/depended/chai"))

