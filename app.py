from flask import Flask, render_template, jsonify, request
from src.helper import download_huggingface_embeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from tqdm.auto import tqdm
import time
from langchain_community.llms import HuggingFaceHub, HuggingFaceEndpoint
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.prompt import *
import os
from store_index import *
from transformers import pipeline 

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'template'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["HUGGINGFACE_API_TOKEN"] = HUGGINGFACE_API_TOKEN

embeddings = download_huggingface_embeddings()
index_name = "medicalbot"

#Embed each chunk and upsert the embeddings into your Pinecone index
try:
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    print(f" Successfully connected to Pinecone index '{index_name}'")
    
    
    index_stats = docsearch._index.describe_index_stats()
    print(f"Index contains {index_stats['total_vector_count']} vectors")
    
    
    batch_size = 100  
    failed_chunks = []
    
    for i in tqdm(range(0, len(text_chunks), batch_size), 
                desc="Embedding medical chunks"):
        batch = text_chunks[i:i + batch_size]
        try:
            docsearch.add_documents(batch)
        except Exception as e:
            print(f" Failed on batch {i//batch_size}: {str(e)}")
            failed_chunks.extend(batch)
    
    if failed_chunks:
        print(f" Failed to embed {len(failed_chunks)} chunks")
        
        from langchain_community.vectorstores import FAISS
        faiss_store = FAISS.from_documents(failed_chunks, embeddings)
        faiss_store.save_local("failed_medical_embeddings")
        print(" Saved failed chunks to local FAISS storage")
    
except Exception as e:
    print(f" Critical error: {str(e)}")
    from langchain_community.vectorstores import FAISS
    faiss_store = FAISS.from_documents(text_chunks, embeddings)
    faiss_store.save_local("full_medical_knowbase")
    print(" All chunks saved to local FAISS storage")

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

llm = HuggingFaceEndpoint(
    repo_id="google/flan-t5-base",
    task="text2text-generation",
    max_length=500,
    temperature=0.4,
    huggingfacehub_api_token=HUGGINGFACE_API_TOKEN
)


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)
test_retrieval = retriever.invoke("What is HIV?")
print("Retrieved Documents:", test_retrieval)

app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/")
def index():
    return render_template("chat.html")

@app.route('/debug')
def debug():
    return {
        "template_folder": app.template_folder,
        "static_folder": app.static_folder,
        "current_directory": os.getcwd(),
        "files_in_template": os.listdir(app.template_folder)
    }

@app.route("/get", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("msg", "").strip()
        
        print(f"\n=== New Query ===\n{msg}")
        
        # Debug: Test direct LLM response
        print("\n[DEBUG] Testing direct LLM response...")
        test_prompt = f"Answer briefly: {msg}"
        direct_response = llm(test_prompt)
        print(f"[DEBUG] Direct Response: {direct_response}")
        
        # Proceed with RAG
        print("\n[DEBUG] Starting RAG processing...")
        start_time = time.time()
        response = rag_chain.invoke({"input": msg})
        elapsed = time.time() - start_time
        
        print(f"\n[DEBUG] RAG Response:")
        print("Full Response Object:", response)
        print("Answer:", response.get("answer", "NO ANSWER FOUND"))
        print(f"Processing Time: {elapsed:.2f}s")
        
        if not response or 'answer' not in response:
            return jsonify({"error": "No response generated"}), 500
            
        return jsonify({"answer": response["answer"]})
        
    except Exception as e:
        print(f"\n[ERROR] Chat endpoint failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
print(f"Current working directory: {os.getcwd()}")
print(f"Template folder path: {os.path.abspath(app.template_folder)}")
print(f"Static folder path: {os.path.abspath(app.static_folder)}")
print(f"chat.html exists: {os.path.exists(os.path.join(app.template_folder, 'chat.html'))}")

# Add this to verify your components are loaded correctly
print("\n=== System Verification ===")
print("Pinecone connection:", "Success" if 'docsearch' in locals() else "Failed")
print("LLM initialization:", "Success" if 'llm' in locals() else "Failed")
print("RAG chain setup:", "Success" if 'rag_chain' in locals() else "Failed")
print("Environment variables:", {
    "PINECONE_API_KEY": bool(PINECONE_API_KEY),
    "HUGGINGFACE_API_TOKEN": bool(HUGGINGFACE_API_TOKEN)
})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)

