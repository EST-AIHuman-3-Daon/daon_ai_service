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

    for path in Path(DOCS_PATH).glob("*.txt"):
        print("FOUND:", path)

        loader = TextLoader(str(path), encoding="utf-8")
        docs.extend(loader.load())

    print("DOC COUNT:", len(docs))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
    )

    chunks = splitter.split_documents(docs)

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