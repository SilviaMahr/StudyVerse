from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from typing import List, Set
from langchain.schema import Document
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Playwright, sync_playwright
from typing import Optional, Dict, Any

CURRICULUM_PDF_PATH = "../docs/1193_17_BS_Wirtschaftsinformatik.pdf"
IDEAL_STUDY_PLAN_PDF_PATH = "../docs/idealtypischerStudienverlauf.pdf"
DOMAIN_BASE = "https://studienhandbuch.jku.at/"
STUDIENHANDBUCH_URL = DOMAIN_BASE + "curr/1193?id=1193&lang=de"
KUSSS_BASE_URL = "https://kusss.jku.at/kusss/"
WIN_ROOT_URL = (
    "https://www.kusss.jku.at/kusss/coursecatalogue-get-segments.action?curId=204&set.listsubjects-overview.treeView.expandedNodes=&set.listsubjects-overview.treeView.expandAll=true"
)

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


def get_links_from_study_manual(url: str = STUDIENHANDBUCH_URL) -> List[Document]:
    embedded_links = []
    try:
        print(f"Hauptseite: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        embedded_links = get_links_from_url(url, response.text)

    except Exception as e:
        print(f"FEHLER beim Laden der URL(s): {e}")

    print(f"--> {len(embedded_links)} eingebettete Links gefunden.")
    return embedded_links


def load_all_curriculum_data() -> List[Document]:
    all_documents = []

    curriculum_pdf = load_pages_from_pdf(CURRICULUM_PDF_PATH)
    all_documents.extend(curriculum_pdf)
    study_plan_pdf = load_pages_from_pdf(IDEAL_STUDY_PLAN_PDF_PATH)
    all_documents.extend(study_plan_pdf)

    url_docs = load_sites_from_url()
    all_documents.extend(url_docs)

    return all_documents


def fetch_content_from_div(url: str) -> Optional[str]:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        target_div = soup.select_one("td.contentcell > div.contentcell")
        selected_option_element = soup.select_one("#term option[selected]")
        semester_html = selected_option_element.text if selected_option_element else ""

        if target_div:
            content_html = str(target_div)

            combined_html = (
                    "<div class='semester-info'>" + semester_html + "</div>\n" +
                    content_html
            )
            print(combined_html[:5000])
            return combined_html

        else:
            print(f"ERROR: Could not find the target div in the HTML for {url}.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching URL {url}: {e}")
        return None

def extract_links(url=WIN_ROOT_URL):
    html = fetch_content_from_div(url)
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    for row in soup.select("tr.darkcell, tr.lightcell"):
        a = row.select_one("a[href]")

        if a:
            link_path = a['href']
            links.append(urljoin(KUSSS_BASE_URL, link_path))

    print(f"Len(cell):  {len(links)}")
    return links


def extract_course_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    lva_links = []

    for a in soup.select("a.normallinkcyan[href]"):
        lva_links.append(urljoin(KUSSS_BASE_URL, a["href"]))

    print(f"Len(cyan): {len(lva_links)} \nlva_links[1]: {lva_links[1]}")
    return lva_links


def extract_win_bsc_info():
    return fetch_content_from_div(WIN_ROOT_URL), WIN_ROOT_URL


def extract_lva_metadata(page):
    metadata = {}

    # --- LVA-Nr. ---
    try:
        metadata["lva_nr"] = page.inner_text("tr.priorityhighlighted a.normallinkcyan").strip()
    except AttributeError:
        metadata["lva_nr"] = None

    # --- LVA Name ---
    try:
        metadata["lva_name"] = page.inner_text("h3 b").split(":")[-1].strip()
    except AttributeError:
        metadata["lva_name"] = None

    # --- ECTS ---
    try:
        ects_text = page.inner_text("text=ECTS").split("ECTS:")[1].split("|")[0]
        metadata["ects"] = float(ects_text.replace(",", "."))
    except AttributeError:
        metadata["ects"] = None

    # --- Semester (W/S) ---
    try:
        selected = page.inner_text("#term option[selected]")
        metadata["semester"] = selected[-1]  # last char (W or S)
    except AttributeError:
        metadata["semester"] = None

    # --- LVA-Leiter ---
    try:
        metadata["lva_leiter"] = page.inner_text("tr.priorityhighlighted td[align='left']").strip()
    except AttributeError:
        metadata["lva_leiter"] = None

    # --- First date row: Tag ---
    try:
        metadata["tag"] = page.inner_text("tr.priorityhighlighted td:nth-child(2)").strip()
    except AttributeError:
        metadata["tag"] = None

    try:
        t = page.inner_text("tr.priorityhighlighted td:nth-child(4)").strip()
        metadata["uhrzeit"] = t.split("(")[0].strip()  # remove (W)
    except AttributeError:
        metadata["uhrzeit"] = None

    return metadata


def extract_lva_metadata_from_manual(page)-> Dict[str, Any]:
    metadata = {}

    try:
        metadata["lva_nr"] = page.inner_text("#code").strip()
    except Exception:
        metadata["lva_nr"] = None

    try:
        header_text = page.inner_text("h3").strip()
        # Beispiel: [ 526GLWN11 ] Studienfach Grundlagen der Wirtschaftsinformatik

        if metadata["lva_nr"]:
             clean_text = header_text.replace(f"[ {metadata['lva_nr']} ]", "").strip()
        else:
             clean_text = header_text

        # LVA-Typ: das erste Wort (Studienfach, Modul) oder die Abkürzung (VL, UE, SE)
        parts = clean_text.split(maxsplit=1)
        if parts:
             metadata["lva_type"] = parts[0].strip()
             metadata["lva_name"] = parts[1].strip() if len(parts) > 1 else clean_text
        else:
             metadata["lva_type"] = None
             metadata["lva_name"] = clean_text

    except Exception:
        metadata["lva_type"] = None
        metadata["lva_name"] = None

    try:
        ects_cell = page.query_selector("table tr.darkcell td:nth-child(1)")

        if ects_cell:
            ects_text = ects_cell.inner_text().strip()
            ects_match = re.search(r'(\d{1,2}(?:,\d{1,2})?)\s*ECTS', ects_text)
            if ects_match:
                 metadata["ects"] = float(ects_match.group(1).replace(",", "."))
            else:
                 metadata["ects"] = None
        else:
             metadata["ects"] = None

    except Exception:
        metadata["ects"] = None

    try:
        leiter_cell = page.query_selector("table tr.darkcell td:nth-child(5)")

        if leiter_cell:
            metadata["lva_leiter"] = leiter_cell.inner_text().strip()
        else:
            metadata["lva_leiter"] = None

    except Exception:
        metadata["lva_leiter"] = None


    try:
        voraus_text = page.inner_text("text=Anmeldevoraussetzungen + td:nth-child(2)")
        metadata["anmeldevoraussetzungen"] = voraus_text.strip()
    except Exception:
        metadata["anmeldevoraussetzungen"] = None

    try:
        sprache_text = page.inner_text("text=Abhaltungssprache + td:nth-child(2)")
        metadata["abhaltungssprache"] = sprache_text.strip()
    except Exception:
        metadata["abhaltungssprache"] = None


    try:
        untergeordnete_elements = page.query_selector_all("ul li a")

        if untergeordnete_elements:
            metadata['untergeordnete_lvas'] = [a.inner_text().strip() for a in untergeordnete_elements]
        else:
            metadata['untergeordnete_lvas'] = None

    except Exception:
        metadata['untergeordnete_lvas'] = None

    return metadata


# Test
if __name__ == "__main__":
    all_docs = load_all_curriculum_data()
    if all_docs:
        print("\nDokumentauszug Test:")
        print(f"Content: {all_docs[0].page_content[:1000]}...")
        print(f"Metadata: {all_docs[0].metadata}")