from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


VECTOR_DB_PATH = "./vector_db"
DOCS_PATH = "./docs"
EMBEDDING_MODEL = "nomic-embed-text"

embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)


def build_vector_db():
    docs = []

    doc_paths = list(Path(DOCS_PATH).glob("*.txt"))
    print("DOC PATHS:", doc_paths)

    if not doc_paths:
        raise Exception(f"No .txt files found in {DOCS_PATH}")

    for path in doc_paths:
        print("FOUND:", path)

        loader = TextLoader(str(path), encoding="utf-8")
        loaded_docs = loader.load()
        print("LOADED:", path, len(loaded_docs))

        docs.extend(loaded_docs)

    print("DOC COUNT:", len(docs))

    if not docs:
        raise Exception("No documents loaded")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
    )

    chunks = splitter.split_documents(docs)
    print("CHUNK COUNT:", len(chunks))

    if not chunks:
        raise Exception("No chunks created. Check document content.")

    vector_db = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    vector_db.save_local(VECTOR_DB_PATH)
    return vector_db


def load_vector_db():
    return FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )


def get_relevant_context(question: str, k: int = 3):
    vector_db = load_vector_db()
    docs = vector_db.similarity_search(question, k=k)

    return "\n\n".join([doc.page_content for doc in docs])