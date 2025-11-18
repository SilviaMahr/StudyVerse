from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain.schema import Document
import re
from html2text import HTML2Text
from data_ingestion.extractor import load_curriculum_data, extract_lva_metadata, extract_metadata_from_sm, extract_lva_metadata_from_manual
#from sentence_transformer import SentenceTransformer

#EMBEDDER = SentenceTransformer('sentence-transformer/all-mpnet-base-v2')

def split_pages_into_chunks(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.split_documents(documents)
    print(f"--> {len(documents)} Dokumentseiten wurden in {len(chunks)} Chunks zerlegt.")

    return chunks


def get_lecture_details(content: str) -> dict:
    # details von Studienhandbuch extrahieren
    # z.B.: 526GLWNEWI13 Einführung in die Wirtschaftsinformatik 6
    details = {}

    lva_code_pattern = r'(526|515)[\w]{6,9}'
    lva_details_match = re.search(
        rf'(?P<lva_code>{lva_code_pattern}) (?P<lva_name>.+?) (?P<ects>\d{{1,2}})',
        content
    )

    if lva_details_match:
        details['lva_code'] = lva_details_match.group('lva_code').strip()
        details['lva_name'] = lva_details_match.group('lva_name').strip()

        try:
            details['ects'] = int(lva_details_match.group('ects')) # cast int
        except ValueError:
            pass

    return details


def get_study_start_mode(content: str) -> str:
    if "mit Beginn im Wintersemester" in content:
        return 'Start_WS'
    elif "mit Beginn im Sommersemester" in content:
        return 'Start_SS'

    # Fallback: über die 1. Semester-Angabe bestimmen
    sem_match = re.search(r'1\.\s*Semester\s*\((?P<ws_ss>WS|SS)\)', content)
    if sem_match:
        return f'Start_{sem_match.group("ws_ss")}'

    return 'Start_Unknown'


def get_ideal_plans(data: Document) -> List[dict]:
    content = data.page_content
    plans = []

    study_start = get_study_start_mode(data.page_content)
    study_mode = 'unknown'
    if "Vollzeit" in content:
        study_mode = 'full_time'
    elif "Teilzeit" in content:
        study_mode = 'part_time'

    semester_match = re.search(r'(?P<sem_num>\d+)\.\s*Semester\s*\((?P<ws_ss>WS|SS)\)', content)
    if semester_match:
        semester_type = semester_match.group('ws_ss')
        semester_num = int(semester_match.group('sem_num'))
    else:
        return []  # Chunk enthält kein klarer Semester-Plan-Teil

    lva_matches = re.findall(
        r'(?P<lva_name>[A-ZÄÖÜa-zäöüß\s,-/()]+?)\s{1,2}(?P<ects>\d{1,2})\s*$',
        content,
        re.MULTILINE
    )

    # print(f"[DEBUG] RegEx fand {len(lva_matches)} mögliche LVA-Matches.")
    # print(f"[DEBUG] Erste 5 Matches: {lva_matches[:5]}")

    for name, ects_val in lva_matches:
        name = name.strip()

        # alles andere ignorieren
        if "Summe" in name or "Semester" in name or "ECTS" in name or name.isspace() or not name:
            continue

        try:
            ects = int(ects_val)
        except ValueError:
            continue

        plans.append({
            'study_start_mode': study_start, # Beginn mit WS oder SS für gesammten Plan
            'study_mode': study_mode, # Vollzeit, Teilzeit
            'semester_type': semester_type, # WS oder SS im Plan
            'semester_num': semester_num, # 1-9
            'lva_name': name,
            'ects': ects,
            'retrieval_type': 'ideal_plan_sequence'
        })

    return plans


def enrich_metadata(data: Document) -> Document:
    content = data.page_content

    # Loader Schlüssel vereinheitlichen
    if 'file_path' in data.metadata:
        data.metadata['source_file'] = data.metadata.pop('file_path')  # PDFLoader als URLLoader

    if 'source' in data.metadata:
        if not data.metadata.get('source_file'):
            data.metadata['source_file'] = data.metadata['source']
        data.metadata.pop('source')

    data.metadata['retrieval_type'] = 'curriculum_facts'

    extracted_details = get_lecture_details(content)
    data.metadata.update(extracted_details)

    source_file = data.metadata.get('source_file', '')

    # für Priorisierung und Semesterzuweisung
    if 'idealtypischerStudienverlauf.pdf' in source_file:
        data.metadata['retrieval_type'] = 'ideal_plan_sequence'
        plan_details = get_ideal_plans(data)

        if plan_details:
            first_lva = plan_details[0]
            data.metadata['semester_type'] = first_lva['semester_type']
            data.metadata['semester_num'] = first_lva['semester_num']

            start_mode = first_lva['study_start_mode']
            if start_mode != 'Start_Unknown':
                data.metadata['study_start_mode'] = start_mode

            study_mode = first_lva['study_mode']
            if study_mode != 'unknown':
                data.metadata['study_mode'] = study_mode

    if '1193_17_BS_Wirtschaftsinformatik.pdf' in source_file:
        # Pflichtfächer
        if 'Fächer und Studienleistungen:' in content:
            data.metadata['retrieval_type'] = 'bachelor_win'

        # Pflichtfächer
        if 'Pflichtfächer zu absolvieren:' in content:
            data.metadata['retrieval_type'] = 'obligatory_lvas'

        # STEOP
        if '§ 6 Studieneingangs- und Orientierungsphase' in content:
            data.metadata['retrieval_type'] = 'steop'

        # Wahlfächer: Regulierung
        if '§ 8 Wahlfächer' in content:
            data.metadata['retrieval_type'] = 'obligatory_elective_lvas'

        # Freie Studienleistungen
        if '§ 9 Freie Studienleistungen' in content:
            data.metadata['retrieval_type'] = 'free_electives'

    # Voraussetzungsketten
    if 'Anmeldevoraussetzungen' in content:
        data.metadata['retrieval_type'] = 'prerequisite_lva'

    # Prüfen, ob eine LVA/ein Modul identifiziert wurde
    data.metadata['has_lva_code'] = 'lva_code' in data.metadata

    return data


def process_documents(documents: List[Document]) -> List[Document]:
    chunks = split_pages_into_chunks(documents)

    processed_data = []

    for data in chunks:
        enriched_data = enrich_metadata(data)
        processed_data.append(enriched_data)

    print(f"--> {len(processed_data)} verarbeitete Chunks bereit für Vektorisierung.")
    return processed_data


def html_to_text(html):
    converter = HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(html)

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=200)
    return splitter.split_text(text)


def chunk_text_with_metadata(text, metadata):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
    chunks = splitter.split_text(text)

    chunks_with_meta = []
    for chunk in chunks:
        chunks_with_meta.append({
            "text": chunk,
            "metadata": metadata
        })

    return chunks_with_meta


def embed_chunks(chunks):
    return EMBEDDER.encode(chunks, convert_to_numpy=True)


def process_html_page(kusss_html, sm_html, semester):
    kusss_metadata = extract_lva_metadata(kusss_html, semester)
    sm_metadata = extract_metadata_from_sm(sm_html)
    kusss_metadata.update(sm_metadata)
    subject_html = kusss_html + sm_html
    text = html_to_text(subject_html)
    chunks = chunk_text_with_metadata(text, kusss_metadata)
    chunks_text = [c["text"] for c in chunks]
    #embeddings = embed_chunks(chunks_text)
    #for i, c in enumerate(chunks):
     #   c["embedding"] = embeddings[i]
    return chunks


def process_sm_html(sm_html):
    sm_metadata = extract_lva_metadata_from_manual(sm_html)
    text = html_to_text(sm_html)
    chunks = chunk_text_with_metadata(text, sm_metadata)
    chunks_text = [c["text"] for c in chunks]
    # embeddings = embed_chunks(chunks_text)
    # for i, c in enumerate(chunks):
    #   c["embedding"] = embeddings[i]
    return chunks


def process_main_page(html):
    text = html_to_text(html)
    chunks = chunk_text(text)
    #embeddings = embed_chunks(chunks)
    return chunks


# Test
if __name__ == "__main__":
    processed_chunks = process_documents(load_curriculum_data())

    if processed_chunks:
        print("\nFinished")