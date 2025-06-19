from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#Extract Data from PDF files
def load_pdf_file(data_path):
    """Load medical PDFs with enhanced error recovery"""
    try:
        loader = DirectoryLoader(
            path=data_path,
            glob="*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True    # Visual loading indicator
        )
        documents = loader.load()
        logger.info(f"Successfully loaded {len(documents)} medical documents")
        return documents
    except Exception as e:
        logger.error(f"Failed to load PDFs: {str(e)}")
        return []
    
# Split the Data into Text Chunks
def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks = text_splitter.split_documents(extracted_data)

    return text_chunks

# Download the Embeddings from HuggingFace
def download_huggingface_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return embeddings
    
