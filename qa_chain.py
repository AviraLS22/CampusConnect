import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA

PDF_DIR = "docs"
VECTORSTORE_DIR = "vectorstore_index"
METADATA_FILE = os.path.join(VECTORSTORE_DIR, "indexed_files.json")

embeddings = OpenAIEmbeddings()

def load_pdfs_as_documents(filenames):
    documents = []
    for filename in filenames:
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(PDF_DIR, filename))
            documents.extend(loader.load())
    return documents

def load_indexed_files():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_indexed_files(file_set):
    with open(METADATA_FILE, "w") as f:
        json.dump(list(file_set), f)

def ensure_vectorstore():
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)
    index_path = os.path.join(VECTORSTORE_DIR, "index.faiss")
    indexed_files = load_indexed_files()
    current_files = set(f for f in os.listdir(PDF_DIR) if f.endswith(".pdf"))

    new_files = current_files - indexed_files

    if os.path.exists(index_path):
        vectorstore = FAISS.load_local(VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True)
    else:
        vectorstore = None

    if new_files:
        print(f"Indexing new files: {new_files}")
        new_docs = load_pdfs_as_documents(new_files)
        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        split_docs = splitter.split_documents(new_docs)

        if vectorstore:
            vectorstore.add_documents(split_docs)
        else:
            vectorstore = FAISS.from_documents(split_docs, embeddings)

        vectorstore.save_local(VECTORSTORE_DIR)
        save_indexed_files(indexed_files.union(new_files))

    elif not os.path.exists(index_path):
        raise ValueError("No index found and no new PDFs to process.")

    return vectorstore

def ask_question(query: str):
    vectorstore = ensure_vectorstore()
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI()
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    return qa_chain.run(query)
