from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from typing import List
from langchain.schema import Document

CURRICULUM_PDF_PATH = "../docs/1193_17_BS_Wirtschaftsinformatik.pdf"
CURRICULUM_URL = "https://studienhandbuch.jku.at/texte/1193_17_BS_Wirtschaftsinformatik.pdf"
STUDIENHANDBUCH_URL = "https://studienhandbuch.jku.at/curr/1193?id=1193&lang=de"

def load_documents_from_pdf(file_path: str = CURRICULUM_PDF_PATH) -> List[Document]:
    try:
        print(f"Pfad für PDF: {file_path}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"--> {len(documents)} Seiten geladen.")
        return documents
    except Exception as e:
        print(f"FEHLER beim Laden der PDF: {e}")
        return []


def load_documents_from_url(url: str = STUDIENHANDBUCH_URL) -> List[Document]:
    try:
        print(f"Pfad für Website: {url}")
        loader = UnstructuredURLLoader(urls=[url])
        documents = loader.load()
        #TODO load all links from Studienhandbuch for subject Prerequisites
        return documents
    except Exception as e:
        print(f"FEHLER beim Laden der URL: {e}")
        return []


def load_all_curriculum_data() -> List[Document]:
    all_documents = []

    pdf_docs = load_documents_from_pdf()
    all_documents.extend(pdf_docs)

    url_docs = load_documents_from_url()
    all_documents.extend(url_docs)

    return all_documents


# Test
if __name__ == "__main__":
    all_docs = load_all_curriculum_data()
    if all_docs:
        print("\nDokumentauszug Test:")
        print(f"Content: {all_docs[0].page_content[:1000]}...")
        print(f"Metadata: {all_docs[0].metadata}")