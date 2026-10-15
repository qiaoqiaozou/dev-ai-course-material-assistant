from urllib.request import urlopen

from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin, urlsplit


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

    paragraphs = [
        element.get_text(" ", strip=True).replace("\u200b", "")
        for element in content.select(
            "h1, h2, h3, h4, p, li, pre, tr"
        )
    ]

    text = "\n\n".join(
        paragraph
        for paragraph in paragraphs
        if paragraph
    )

    if not text:
        raise ValueError("The page does not contain readable text.")

    return {
        "title": title,
        "course": course,
        "url": url,
        "text": text,
    }

def find_chapter_urls(home_url):
    with urlopen(home_url, timeout=30) as response:
        html = response.read().decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")

    home = urlsplit(home_url)
    chapter_path = home.path.rstrip("/") + "/docs/chapters/"

    chapters = {}
    chapter_numbers = [
        "01", "02", "03", "04",
        "05", "06", "07", "08",
    ]

    for link in soup.find_all("a", href=True):
        url = urljoin(home_url, link["href"])
        url, _ = urldefrag(url)

        parsed = urlsplit(url)

        if parsed.scheme != home.scheme or parsed.netloc != home.netloc:
            continue

        if not parsed.path.startswith(chapter_path):
            continue

        slug = parsed.path[len(chapter_path):].strip("/")
        number = slug.split("-")[0]

        if number in chapter_numbers and "/" not in slug:
            chapters[number] = url

    if len(chapters) != 8:
        raise ValueError("Could not find all eight chapter links.")

    return [
        chapters[number]
        for number in chapter_numbers
    ]


def load_course_documents(home_url, course="DEV-AI"):
    documents = []

    for url in find_chapter_urls(home_url):
        document = load_web_document(url, course=course)
        documents.append(document)

    return documents