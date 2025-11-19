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