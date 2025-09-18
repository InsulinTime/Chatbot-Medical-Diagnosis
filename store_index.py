#this file is store_index.py
from src.helper import load_pdf_file, text_split, download_huggingface_embeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from tqdm.auto import tqdm
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY


extracted_data = load_pdf_file(data_path="Data/")
text_chunks = text_split(extracted_data)
embeddings = download_huggingface_embeddings()

pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "medicalbot"
dimension = 384  


if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    print(f"Created new index: {index_name}")
else:
    print(f"Index {index_name} already exists")

# Embed each chunk and upsert the embeddings into your Pinecone index
try:
    
    docsearch = PineconeVectorStore.from_documents(
        documents=text_chunks,
        embedding=embeddings,
        index_name=index_name,
        batch_size=100,
        namespace="medical_knowledge",
    )
    print("Successfully embedded all chunks!")
    
except Exception as e:
    print(f" Embedding failed: {str(e)}")
    
    from langchain_community.vectorstores import FAISS
    faiss_store = FAISS.from_documents(text_chunks, embeddings)
    faiss_store.save_local("medical_chatbot_fallback")
    print("Saved embeddings locally as fallback")

