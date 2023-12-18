from os import environ
import re
import shutil
from pathlib import Path
from bs4 import BeautifulSoup as bs
import readability
import requests
from requests.packages.urllib3.util import retry
import feedparser


def parse(html):
    document = readability.Document(html)
    partial_html = document.summary(html_partial=True)
    all_text = bs(partial_html, "html.parser").find_all(
        string=True
    )
    return " ".join(all_text)


def slugify(name):
    return re.sub(r"[^a-z]+", "-", name.lower())


def get_session():
    retries = 5
    backoff_factor = 0.3

    session = requests.Session()
    r = retry.Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=r)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    proxy = environ.get("PROXY")
    if proxy:
        PROXIES = {
            "http": proxy,
            "https": proxy,
        }
        session.proxies.update(PROXIES)
    return session


def fetch(url, session):
    resp = session.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:67.0) Gecko/20100101 Firefox/67.0"
        }
    )
    return resp.content


if __name__ == "__main__":
    output_folder = "docs"
    shutil.rmtree("docs", ignore_errors=True)
    shutil.copytree("_docs", output_folder)

    with open("SOURCES.txt") as fh:
        lines = fh.read()

    session = get_session()

    for feed_url in lines.split("\n"):
        parsed = feedparser.parse(feed_url)
        if parsed["entries"] == []:
            print(f"Failed to parse {feed_url}")
            continue
        title = parsed["feed"]["title"]
        slug = slugify(title)
        url = parsed["entries"][0]["link"]
        source_html = fetch(url, session)
        try:
            parsed = parse(source_html)
        except readability.readability.Unparseable:
            continue
        root_path = Path(output_folder)
        fp = root_path / f"{slug}"
        fp.mkdir(exist_ok=True, parents=True)
        with open(fp / "source.html", "wb") as fh:
            fh.write(source_html)
        with open(fp / "index.html", "w") as fh:
            fh.write(f'---\ntitle: "{title}"\nsource_url: {url}\n---\n\n{parsed}')
