from bs4 import BeautifulSoup
import requests
import time
import random

TOKEN = "GITHUB ACCESS TOKEN HERE" # 5k requests per hour

# Getting github link from https://www.npmjs.com/package/chai
def get_github_from_npm_link(url):
    response = requests.get(url)
    if response.status_code != 200: # Most likely link from npm 404'd
        print("Error in request to ", url, response.status_code)
        print(response.text)
        print("Sleeping for 5 minutes then trying again")
        time.sleep(300)
        return get_github_from_npm_link(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return find_github_url(soup)

def find_github_url(soup):
    github_section = soup.find(match_repository_link)
    if github_section is None:
        print("No repo link found")
        return None
    return github_section.find_next_sibling().find('a')['href']

def match_repository_link(soup):
    return soup.name == "h3" and soup.get_text() == "Repository"

# Getting links from https://www.npmjs.com/browse/depended/chai
def get_dependent_links_from_url(url):
    response = requests.get(url)
    if response.status_code != 200: # Most likely link from npm 404'd
        print("Error in request to ", url, response.status_code)
        print(response.text)
        print("Sleeping for 5 minutes then trying again")
        time.sleep(300)
        return get_dependent_links_from_url(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return find_all_dependents_on_page(soup)

def find_all_dependents_on_page(soup):
    sections = soup.find_all('section')
    a_elems = [section.find(match_npm_link_from_dependents) for section in sections]
    return ["https://www.npmjs.com/" + elem['href'] for elem in a_elems]

def match_npm_link_from_dependents(soup):
    return soup.name == 'a' and soup.find('h3') is not None

# Getting stars from https://github.com/chaijs/chai
def get_stars_from_url(url):
    if not "github.com" in url:
        print("Repo link not to github")
        return None
    new_url = url.replace("https://github.com", "https://api.github.com/repos")
    response = None
    try:
        response = requests.get(new_url, headers={'Authorization': 'token %s' % TOKEN})
    except Exception as e:
        return None # Poorly formatted url
    if response.status_code != 200: # Most likely link from npm 404'd
        print("Error in request to ", new_url)
        print(response.status_code, response.json()["message"])
        return None
    return response.json()["stargazers_count"]

def get_github_and_stars_from_dependents_page(url):
    print("Requesting dependent links")
    links = get_dependent_links_from_url(url)
    if links is None:
        return []

    repos = []
    for link in links:
        # Sleeping a bit out of rate-limit/bot-detection caution
        time.sleep(random.random()) # 0-1 second
        print("Requesting npm page")
        repo = get_github_from_npm_link(link)
        if repo is not None:
            repos.append(repo)

    pairs = []
    for repo in repos:
        print("Requesting stars")
        stars = get_stars_from_url(repo)
        if stars is not None:
            pairs.append((repo, stars))

    return pairs

def second_item(elem):
    return elem[1]

def main(url_base, offset = 0):
    print("Main iteration at offset %d" % offset)
    url = url_base + "?offset=%d" % offset
    results = get_github_and_stars_from_dependents_page(url)
    with open("./results.txt", "w+") as f:
        for result in results:
            f.write("%s %s\n" % (result[0], result[1]))

    if offset > 50:
        return
    return main(url_base, offset + 36)

with open("./results.txt", "w") as f: # Just wipe the file at the start
    f.write("")

main("https://www.npmjs.com/browse/depended/chai")