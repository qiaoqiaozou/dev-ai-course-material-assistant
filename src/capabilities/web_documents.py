from urllib.request import urlopen

from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin, urlsplit
from xml.etree import ElementTree


def load_web_document(url, course="DEV-AI"):
    with urlopen(url, timeout=30) as response:
        html = response.read().decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")

    content = soup.select_one(".theme-doc-markdown")

    if content is None:
        raise ValueError("The page does not contain the expected course content.")

    heading = content.find("h1")

    if heading is None:
        raise ValueError("The page does not contain a title.")

    title = heading.get_text(" ", strip=True).replace("\u200b", "")

    for element in content.select("script, style, .hash-link"):
        element.decompose()

    

    text = content.get_text(
        separator="\n\n",
        strip=True,
    ).replace("\u200b", "")

    if not text:
        raise ValueError("The page does not contain readable text.")

    return {
        "title": title,
        "course": course,
        "url": url,
        "text": text,
    }

def find_course_urls(home_url):
    home = urlsplit(home_url)
    docs_path = home.path.rstrip("/") + "/docs/"
    sitemap_url = urljoin(home_url.rstrip("/") + "/", "sitemap.xml")

    with urlopen(sitemap_url, timeout=30) as response:
        sitemap = ElementTree.fromstring(response.read())

    namespace = {
        "sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9",
    }

    urls = set()

    for location in sitemap.findall("sitemap:url/sitemap:loc", namespace):
        url = (location.text or "").strip()
        parsed = urlsplit(url)

        if parsed.scheme != home.scheme or parsed.netloc != home.netloc:
            continue

        if not parsed.path.startswith(docs_path):
            continue

        url = parsed._replace(query="", fragment="").geturl()
        urls.add(url.rstrip("/"))

    if not urls:
        raise ValueError("Could not find course document links.")

    return sorted(urls)


def load_course_documents(home_url, course="DEV-AI"):
    documents = []

    for url in find_course_urls(home_url):
        document = load_web_document(url, course=course)
        documents.append(document)

    return documents