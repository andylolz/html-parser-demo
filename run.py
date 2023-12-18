import re
import shutil
from pathlib import Path
from bs4 import BeautifulSoup as bs
import readability
import requests
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


if __name__ == "__main__":
    output_folder = "docs"
    shutil.rmtree("docs", ignore_errors=True)
    shutil.copytree("_docs", output_folder)
    with open("SOURCES.txt") as fh:
        lines = fh.read()
    for feed_url in lines.split("\n"):
        parsed = feedparser.parse(feed_url)
        if parsed["entries"] == []:
            print(f"Failed to parse {feed_url}")
            continue
        title = parsed["feed"]["title"]
        slug = slugify(title)
        url = parsed["entries"][0]["link"]
        r = requests.get(url)
        source_html = r.content
        try:
            parsed = parse(source_html)
        except readability.readability.Unparseable:
            continue
        root_path = Path(output_folder)
        fp = root_path / f"{slug}"
        fp.mkdir(exist_ok=True, parents=True)
        with open(fp / "source.html", "wb") as fh:
            fh.write(source_html)
        with open(fp / "index.md", "w") as fh:
            fh.write(f'---\ntitle: "{title}"\nsource_url: {url}\n---\n\n{parsed}')
