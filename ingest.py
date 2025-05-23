from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

def ingest_docs():
    loader = PyPDFLoader("docs/rulebook.pdf")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = splitter.split_documents(docs)
    db = FAISS.from_documents(splits, OpenAIEmbeddings())
    db.save_local("data/")

if __name__ == "__main__":
    ingest_docs()
