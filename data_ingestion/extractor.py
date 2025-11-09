from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from typing import List, Set
from langchain.schema import Document
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

CURRICULUM_PDF_PATH = "../docs/1193_17_BS_Wirtschaftsinformatik.pdf"
IDEAL_STUDY_PLAN_PDF_PATH = "../docs/idealtypischerStudienverlauf.pdf"
DOMAIN_BASE = "https://studienhandbuch.jku.at/"
STUDIENHANDBUCH_URL = DOMAIN_BASE + "curr/1193?id=1193&lang=de"

def load_pages_from_pdf(file_path: str) -> List[Document]:
    try:
        print(f"Pfad für PDF: {file_path}")
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        print(f"--> {len(pages)} Seiten geladen.")
        return pages
    except Exception as e:
        print(f"FEHLER beim Laden der PDF: {e}")
        return []

def get_links_from_url(url: str, content: str) -> Set[str]:
    links = set()
    # Basis-Link gefolgt von mindestens einer Ziffer
    link_pattern = re.compile(r"^" + re.escape(DOMAIN_BASE) + r"\d+$")
    try:
        soup = BeautifulSoup(content, 'html.parser')

        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            absolute_url = urljoin(url, href)

            if link_pattern.match(absolute_url):
                links.add(absolute_url)

    except Exception as e:
        print(f"Fehler während Parsen der links von {url}: {e}")

    return links


def load_sites_from_url(url: str = STUDIENHANDBUCH_URL) -> List[Document]:
    all_webpages = []

    try:
        print(f"Hauptseite: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        embedded_links = get_links_from_url(url, response.text)
        print(f"--> {len(embedded_links)} eingebettete Links gefunden.")
        #print(f"Beispiellink: {list(embedded_links)[31]}")

        urls_to_load = list(embedded_links)
        urls_to_load.append(url)

        loader = UnstructuredURLLoader(urls=urls_to_load)
        webpages = loader.load()

        all_webpages.extend(webpages)

    except Exception as e:
        print(f"FEHLER beim Laden der URL(s): {e}")

    print(f"--> {len(all_webpages)} Dokumente geladen.")
    return all_webpages


def load_all_curriculum_data() -> List[Document]:
    all_documents = []

    curriculum_pdf = load_pages_from_pdf(CURRICULUM_PDF_PATH)
    all_documents.extend(curriculum_pdf)
    study_plan_pdf = load_pages_from_pdf(IDEAL_STUDY_PLAN_PDF_PATH)
    all_documents.extend(study_plan_pdf)

    url_docs = load_sites_from_url()
    all_documents.extend(url_docs)

    return all_documents


# Test
if __name__ == "__main__":
    all_docs = load_all_curriculum_data()
    if all_docs:
        print("\nDokumentauszug Test:")
        print(f"Content: {all_docs[0].page_content[:1000]}...")
        print(f"Metadata: {all_docs[0].metadata}")