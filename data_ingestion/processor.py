"""
This script serves as the 'Transform' layer of the ETL pipeline. It focuses on:
1. Cleaning raw data (HTML to Text conversion).
2. Segmenting documents and text into manageable pieces (Chunking).
3. Enriching data with metadata (LVA codes, ECTS, retrieval types).
4. Generating vector embeddings using a provided model.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document
import re
import os
from html2text import HTML2Text
from data_ingestion.extractor import (load_curriculum_data,
                                      extract_lva_metadata,
                                      extract_metadata_from_sm,
                                      extract_lva_metadata_from_manual)


def split_pages_into_chunks(documents: List[Document]) -> List[Document]:
    """
    Splits large document pages into smaller text segments.
    INPUT: documents (List[Document]) - List of raw document pages.
    OUTPUT: List[Document] - List of chunked document segments.
    """
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
    """
    Extracts details from Study Manual: Uses regex to extract LVA code, name, and ECTS from raw text.
    INPUT: content (String) - The text of a chunk.
    OUTPUT: dict - Extracted keys (lva_code, lva_name, ects).
    e.g., 526GLWNEWI13 Einführung in die Wirtschaftsinformatik 6
    """
    details = {}

    # Matches JKU-specific course codes starting with 526 or 515.
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
    """
    Standardizes source paths and assigns 'retrieval_type' based on text keywords.
    INPUT: data (Document) - A single document chunk.
    OUTPUT: Document - The chunk with updated metadata.
    """
    content = data.page_content

    # Loader key unification: Unifies metadata keys from different loaders
    if 'file_path' in data.metadata:
        data.metadata['source_file'] = data.metadata.pop('file_path')  # PDFLoader as URLLoader

    if 'source' in data.metadata:
        if not data.metadata.get('source_file'):
            data.metadata['source_file'] = data.metadata['source']
        data.metadata.pop('source')

    # retrieval_type - Labels the chunk for targeted RAG retrieval (e.g., 'steop', 'free_electives').
    data.metadata['retrieval_type'] = 'curriculum_facts'

    extracted_details = get_lecture_details(content)
    data.metadata.update(extracted_details)

    source_file = data.metadata.get('source_file', '')

    if '1193_17_BS_Wirtschaftsinformatik.pdf' in source_file:
        # Compulsory courses
        if 'Fächer und Studienleistungen:' in content:
            data.metadata['retrieval_type'] = 'bachelor_win'

        # Compulsory courses
        if 'Pflichtfächer zu absolvieren:' in content:
            data.metadata['retrieval_type'] = 'obligatory_lvas'

        # STEOP
        if '§ 6 Studieneingangs- und Orientierungsphase' in content:
            data.metadata['retrieval_type'] = 'steop'

        # Electives: Regulation
        if '§ 8 Wahlfächer' in content:
            data.metadata['retrieval_type'] = 'obligatory_elective_lvas'

        # Free elective courses
        if '§ 9 Freie Studienleistungen' in content:
            data.metadata['retrieval_type'] = 'free_electives'

    return data


def process_documents(documents: List[Document], model) -> (List[Document], List[List[float]]):
    """
    Complete processing pipeline for PDF documents.
    INPUT: documents (List[Document]), model (Embedding Model).
    OUTPUT: (List[Document], List[List[float]]) - Processed chunks and their vectors.
    """
    chunks = split_pages_into_chunks(documents)

    processed_chunks = []
    chunks_text = []

    for chunk in chunks:
        enriched_chunk = enrich_metadata(chunk)
        processed_chunks.append(enriched_chunk)

        chunks_text.append(enriched_chunk.page_content)

    try:
        # Generates vector representations for all chunks in a single batch call.
        embeddings = model.embed_documents(chunks_text)
    except Exception as e:
        print(f"FATALER FEHLER bei der Vektorisierung: {e}")
        return [], []

    print(f"--> {len(processed_chunks)} verarbeitete Chunks bereit.")
    return processed_chunks, embeddings

def html_to_text(html):
    """
    Converts raw HTML into clean, readable Markdown-like text.
    INPUT: html (String).
    OUTPUT: str - Cleaned text.
    """
    converter = HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(html)

def chunk_text(text):
    """
    Simple text splitter for raw strings.
    INPUT: text (String).
    OUTPUT: List[str] - List of text strings.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=200)
    return splitter.split_text(text)


def chunk_text_with_metadata(text, metadata):
    """
    Splits text and attaches a specific metadata object to every resulting chunk.
    INPUT: text (String), metadata (Dictionary).
    OUTPUT: List[dict] - List of dictionaries containing "text" and "metadata".
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
    chunks = splitter.split_text(text)

    chunks_with_meta = []
    for chunk in chunks:
        chunks_with_meta.append({
            "text": chunk,
            "metadata": metadata
        })

    return chunks_with_meta


def process_html_page(kusss_html, sm_html, semester, model):
    """
    Processes Course (LVA) data by combining KUSSS and Study Manual HTML.
    INPUT: kusss_html, sm_html, semester, model.
    OUTPUT: List[dict] - List of chunks containing text, metadata, and embeddings.
    """
    kusss_metadata = extract_lva_metadata(kusss_html, semester)
    sm_metadata = extract_metadata_from_sm(sm_html)
    kusss_metadata.update(sm_metadata)
    subject_html = kusss_html + sm_html
    text = html_to_text(subject_html)
    chunks = chunk_text_with_metadata(text, kusss_metadata)
    chunks_text = [c["text"] for c in chunks]
    try:
        embeddings = model.embed_documents(chunks_text)
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
    except Exception as e:
        print(f"FATALER FEHLER bei der Vektorisierung: {e}")
        return []
    return chunks


def process_sm_html(sm_html, model):
    """
    Processes standalone Study Manual HTML pages.
    INPUT: sm_html, model.
    OUTPUT: List[dict] - Chunks enriched with manual metadata and embeddings.
    """
    sm_metadata = extract_lva_metadata_from_manual(sm_html)
    text = html_to_text(sm_html)
    chunks = chunk_text_with_metadata(text, sm_metadata)
    chunks_text = [c["text"] for c in chunks]
    try:
        embeddings = model.embed_documents(chunks_text)
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
    except Exception as e:
        print(f"FATALER FEHLER bei der Vektorisierung: {e}")
        return []
    return chunks


def process_main_page(html, model):
    """
    Processes generic HTML pages (e.g., landing pages) without specific metadata extraction.
    INPUT: html, model.
    OUTPUT: List[dict] - Raw text chunks with empty metadata and embeddings.
    """
    text = html_to_text(html)
    chunks_text = chunk_text(text)
    try:
        embeddings = model.embed_documents(chunks_text)
        chunks = []
        for i, text_chunk in enumerate(chunks_text):
            chunks.append({
                "text": text_chunk,
                "metadata": {},
                "embedding": embeddings[i]
            })
    except Exception as e:
        print(f"FATALER FEHLER bei der Vektorisierung: {e}")
        return []
    return chunks


# Test
if __name__ == "__main__":
    processed_chunks = process_documents(load_curriculum_data())

    if processed_chunks:
        print("\nFinished")