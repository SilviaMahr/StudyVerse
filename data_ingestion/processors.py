from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain.schema import Document
import re

from data_ingestion.loaders import load_all_curriculum_data


def split_documents_into_chunks(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    # Website?
    #html_splitter = HTMLTextSplitter(
    #    chunk_size=100,
    #    chunk_overlap=20
    #)

    print("Starte Chunking...")
    chunks = text_splitter.split_documents(documents)
    print(f"--> {len(documents)} Dokumentseiten wurden in {len(chunks)} Chunks zerlegt.")

    return chunks

# Test
if __name__ == "__main__":
    processed_chunks = split_documents_into_chunks(load_all_curriculum_data())

    if processed_chunks:
        print("\nFinished")
        print(processed_chunks[54])
