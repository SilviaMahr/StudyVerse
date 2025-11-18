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
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        embedded_links = get_links_from_url(url, response.text)

    except Exception as e:
        print(f"FEHLER beim Laden der URL(s): {e}")

    print(f"--> {len(embedded_links)} eingebettete Links gefunden.")
    return embedded_links


def load_curriculum_data() -> List[Document]:
    return load_pages_from_pdf(CURRICULUM_PDF_PATH)


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
                    "<div class='semester-tobe-planned'>" + semester_html + "</div>\n" +
                    content_html
            )
            return combined_html

        else:
            print(f"ERROR: Could not find the target div in the HTML for {url}.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching URL {url}: {e}")
        return None


def extract_links(**kwargs):
    html = ""
    if kwargs.get("url"):
        html = fetch_content_from_div(kwargs.get("url"))
    elif kwargs.get("html"):
        html = kwargs.get("html")

    soup = BeautifulSoup(html, 'html.parser')
    links = []

    for row in soup.select("tr.darkcell, tr.lightcell"):
        a_lva = row.select_one("td:nth-child(2) a[href]")

        if a_lva:
            link_path = a_lva['href']
            links.append(urljoin(KUSSS_BASE_URL, link_path))

        a_study_manual = row.select_one("td:last-child a[href]")

        if a_study_manual and a_study_manual['href'].startswith('https'):
            links.append(a_study_manual['href'])
    return links


def extract_lva_links_for_course(html):
    soup = BeautifulSoup(html, 'html.parser')
    lva_links = []
    lva_nrs = []

    # check if the course is offered in the selected semester
    message_element = soup.select_one("p.message")

    if message_element:
        message_text = message_element.text.strip()
        return {
            "lva_links": [],
            "semester_msg": message_text
        }

    lva_link_selector = "tr.darkcell td:first-child a.normallinkcyan[href], tr.lightcell td:first-child a.normallinkcyan[href]"

    for a in soup.select(lva_link_selector):

        lva_nr = a.text.strip()

        if '.' in lva_nr:
            lva_nrs.append(lva_nr)
            lva_links.append(urljoin(KUSSS_BASE_URL, a["href"]))

    return {
        "lva_links": lva_links,
        "semester_msg": ""
    }


def extract_win_bsc_info():
    return fetch_content_from_div(WIN_ROOT_URL), WIN_ROOT_URL


def extract_semester_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    div_element = soup.select_one("div.semester-tobe-planned")

    if div_element:
        text_content = div_element.text.strip()

        if text_content:
            last_char = text_content[-1]
            return last_char +"S"
        else:
            return None
    else:
        return None


def extract_lva_metadata(html, semester):
    soup = BeautifulSoup(html, 'html.parser')
    metadata = {}

    # --- LVA-Nr. ---
    try:
        lva_nr_element = soup.select_one("tr.priorityhighlighted a.normallinkcyan")
        if lva_nr_element:
            metadata["lva_nr"] = lva_nr_element.text.strip()
        else:
            metadata["lva_nr"] = None # not offered in the given semester
    except Exception:
        metadata["lva_nr"] = None

    # --- LVA Type ---
    try:
        lva_type_abbr = soup.select_one("h3 abbr")
        if lva_type_abbr:
            short_type = lva_type_abbr.get_text(strip=True)
            metadata["lva_type"] = short_type
        else:
            metadata["lva_type"] = None
    except Exception:
        metadata["lva_type"] = None

    # --- LVA Name ---
    try:
        lva_name_element = soup.select_one("h3 b")
        if lva_name_element:
            metadata["lva_name"] = lva_name_element.text.split(":")[-1].strip()
        else:
            metadata["lva_name"] = None
    except Exception:
        metadata["lva_name"] = None

    # --- ECTS ---
    try:
        # <td ...> ECTS: X.X | ... </td>
        ects_element = soup.find(lambda tag: tag.name == 'td' and 'ECTS:' in tag.text)
        if ects_element:
            # the text between "ECTS:" and "|"
            ects_text = ects_element.text.split("ECTS:")[1].split("|")[0].strip()
            metadata["ects"] = float(ects_text.replace(",", "."))
        else:
            metadata["ects"] = None
    except Exception:
        metadata["ects"] = None

    # --- Semester (WS/SS) ---
    metadata["semester"] = semester

    # --- LVA-Leiter ---
    try:
        leiter_element = soup.select_one("tr.priorityhighlighted td[align='left']")
        if leiter_element:
            metadata["lva_leiter"] = leiter_element.text.strip()
        else:
            metadata["lva_leiter"] = None
    except Exception:
        metadata["lva_leiter"] = None

    termin_table = soup.find("table", summary=lambda s: s and "Übersicht aller Termine der Lehrveranstaltung" in s)
    if termin_table:
        first_row = termin_table.select_one("tr.darkcell, tr.lightcell")

        if first_row:
            try:
                # --- Tag ---
                tag_element = first_row.select_one("td:nth-child(1)")
                if tag_element:
                    metadata["tag"] = tag_element.text.strip()
                else:
                    metadata["tag"] = None
            except Exception:
                metadata["tag"] = None

            try:
                # --- Uhrzeit ---
                uhrzeit_element = first_row.select_one("td:nth-child(3)")
                if uhrzeit_element:
                    metadata["uhrzeit"] = uhrzeit_element.text.strip()
                else:
                    metadata["uhrzeit"] = None
            except Exception:
                metadata["uhrzeit"] = None

    else:
        try:
            tag_element = soup.select_one("tr.priorityhighlighted td:nth-child(2)")
            if tag_element:
                metadata["tag"] = tag_element.text.strip()
            else:
                metadata["tag"] = None
        except Exception:
            metadata["tag"] = None


        try:
            uhrzeit_element = soup.select_one("tr.priorityhighlighted td:nth-child(4)")
            if uhrzeit_element:
                t = uhrzeit_element.text.strip()
                metadata["uhrzeit"] = t.split("(")[0].strip()
            else:
                metadata["uhrzeit"] = None
        except Exception:
            metadata["uhrzeit"] = None

    return metadata


def extract_metadata_from_sm(html)-> Dict[str, Any]:
    soup = BeautifulSoup(html, 'html.parser')
    metadata = {}

    try:
        lva_code_element = soup.select_one("#code")
        if lva_code_element:
            metadata["lva_code"] = lva_code_element.get_text(strip=True)
        else:
            metadata["lva_code"] = None
    except Exception:
        metadata["lva_code"] = None

    try:
        leiter_cell = soup.select_one("table tr.darkcell td:nth-child(5)")

        if leiter_cell:
            metadata["lva_verantwortlicheR"] = leiter_cell.get_text(strip=True)
        else:
            metadata["lva_verantwortlicheR"] = None
    except Exception:
        metadata["lva_verantwortlicheR"] = None

    try:
        voraus_key_cell = soup.find("td", string=lambda t: t and "Anmeldevoraussetzungen" in t)

        if voraus_key_cell and voraus_key_cell.next_sibling:
            value_cell = voraus_key_cell.find_next_sibling('td')
            if value_cell:
                metadata["anmeldevoraussetzungen"] = value_cell.get_text(strip=True)
            else:
                metadata["anmeldevoraussetzungen"] = None
        else:
            metadata["anmeldevoraussetzungen"] = None
    except Exception:
        metadata["anmeldevoraussetzungen"] = None

    try:
        sprache_key_cell = soup.find("td", string=lambda t: t and "Abhaltungssprache" in t)

        if sprache_key_cell and sprache_key_cell.next_sibling:
            value_cell = sprache_key_cell.find_next_sibling('td')
            if value_cell:
                metadata["abhaltungssprache"] = value_cell.get_text(strip=True)
            else:
                metadata["abhaltungssprache"] = None
        else:
            metadata["abhaltungssprache"] = None

    except Exception:
        metadata["abhaltungssprache"] = None

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
        leiter_cell = page.query_selector("table tr.darkcell td:nth-child(4)")

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
        metadata["anmeldevoraussetzungen"] = "keine"

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
    all_docs = load_curriculum_data()
    if all_docs:
        print("\nDokumentauszug Test:")
        print(f"Content: {all_docs[0].page_content[:1000]}...")
        print(f"Metadata: {all_docs[0].metadata}")