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
from src.prompt import system_prompt, enhance_response
import os
from store_index import *
from transformers import pipeline 
from src.helper import load_medical_disease_data
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

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
medical_disease_data = load_medical_disease_data()

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

def find_matching_disease(user_input: str) -> Optional[Dict[str, Any]]:
    """Find matching disease using improved matching logic."""
    user_input = user_input.lower()
    
    for name, data in medical_disease_data.items():
        if name.lower() in user_input:
            return data
    
    for name, data in medical_disease_data.items():
        if name.lower().replace(" ", "") in user_input.replace(" ", ""):
            return data
    
    symptom_counts = {}
    for name, data in medical_disease_data.items():
        for symptom in data.get('symptoms', []):
            if symptom.lower() in user_input:
                symptom_counts[name] = symptom_counts.get(name, 0) + 1
    
    if symptom_counts:
        best_match = max(symptom_counts.items(), key=lambda x: x[1])
        if best_match[1] >= 2: 
            return medical_disease_data[best_match[0]]
    
    return None

def format_disease_response(disease_info: Dict[str, Any], rag_context: str = "") -> str:
    """Format disease information into a structured response with South African context."""
    sections = [
        ("Symptoms", "symptoms", "sa-green"),
        ("How It's Contracted", "how_contracted", "sa-yellow"),
        ("Diagnosis", "diagnosis", "sa-blue"),
        ("Treatment", "treatment", "sa-blue"),
        ("Prevention", "prevention", "sa-green"),
        ("High Risk Areas in SA", "high_risk_areas", "sa-red")
    ]
    
    response = [
        f"<div class='disease-header'><strong>{disease_info['name'].title()}</strong>",
        f"<em>{disease_info['description']}</em></div>"
    ]
    
    if rag_context:
        response.extend([
            "<div class='additional-info'><strong>Additional Information:</strong>",
            f"<p>{rag_context}</p></div>"
        ])
    
    for title, key, color_class in sections:
        content = disease_info.get(key)
        if content:
            response.append(f"<div class='disease-section {color_class}'><strong>{title}:</strong>")
            if isinstance(content, list):
                response.append("<ul>")
                response.extend(f"<li>{item}</li>" for item in content)
                response.append("</ul>")
            else:
                response.append(f"<p>{content}</p>")
            response.append("</div>")
    
    sa_guidance = get_south_africa_guidance(disease_info)
    response.extend([
        "<div class='sa-guidance'><strong>For South African Clinics:</strong>",
        f"<p>{sa_guidance}</p></div>"
    ])
    
    if disease_info.get('urgent'):
        response.extend([
            "<div class='urgent-warning'><strong>URGENT:</strong>",
            "<p>This condition may require immediate medical attention. Please seek care now if you have:</p>",
            "<ul>",
            *[f"<li>{symptom}</li>" for symptom in disease_info['urgent_symptoms']],
            "</ul></div>"
        ])
    
    return "".join(response)

def get_clinic_info(location: str) -> str:
    """Generate mock clinic information based on location"""
    clinics = {
        "johannesburg": [
            {
                "name": "Johannesburg Central Clinic",
                "address": "123 Health St, Johannesburg, 2000",
                "hours": "Mon-Fri: 7:30AM-4PM, Sat: 8AM-12PM",
                "phone": "011 123 4567"
            }
        ],
        "cape town": [
            {
                "name": "Cape Town District Health Facility",
                "address": "789 Wellness Rd, Cape Town, 8000",
                "hours": "Mon-Fri: 8AM-5PM",
                "phone": "021 987 6543"
            }
        ]
    }
    
    location_key = location.lower()
    if location_key in clinics:
        clinic_list = []
        for clinic in clinics[location_key]:
            clinic_list.append(
                f"<div class='clinic-card'>"
                f"<div class='clinic-name'>{clinic['name']}</div>"
                f"<div class='clinic-address'>{clinic['address']}</div>"
                f"<div class='clinic-hours'><i class='far fa-clock'></i> {clinic['hours']}</div>"
                f"<div class='clinic-phone'><i class='fas fa-phone'></i> {clinic['phone']}</div>"
                f"</div>"
            )
        return (
            f"<h4>Clinics near {location.title()}:</h4>"
            + "".join(clinic_list)
            + "<p>Remember to bring your ID and medical card if you have one.</p>"
        )
    return f"I couldn't find clinics in {location}. Please try a nearby city name."

def get_south_africa_guidance(disease_info: Dict[str, Any]) -> str:
    """Generate South Africa-specific guidance for a disease."""
    name = disease_info['name'].lower()
    
    guidance_map = {
        'hiv': "ART medications available at all public clinics. CD4 testing requires referral.",
        'aids': "Advanced care available at district hospitals. Support groups widely available.",
        'malnutrition': "Nutritional supplements at primary clinics. Severe cases to district hospitals.",
        'asthma': "Inhalers available at clinics. Emergency care at community health centers.",
        'gonorrhea': "Treatment available at all clinics. Partner notification services provided."
    }
    
    return guidance_map.get(name, 
        "Standard treatment available at primary healthcare clinics. Severe cases should be referred.")

llm = pipeline (
    task="text2text-generation",
    model="google/flan-t5-large",
    token=os.getenv("HUGGINGFACE_API_TOKEN"),
    max_length=9000,
    temperature=0.6,
    top_p=0.95,
    top_k=50,
    do_sample=True)

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
        if not data or 'msg' not in data:
            return jsonify({"error": "Invalid request format"}), 400
            
        user_input = data.get("msg", "").strip()
        if not user_input:
            return jsonify({"error": "Empty message"}), 400
        
        # Check for disease match
        disease_info = find_matching_disease(user_input)
        
        if disease_info:
            # Get supplemental context from RAG
            docs = retriever.invoke(disease_info['name'])[:1]
            rag_context = docs[0].page_content[:300] if docs else ""
            
            response = format_disease_response(disease_info, rag_context)
            return jsonify({"answer": response})
        
        # Standard RAG flow
        docs = retriever.invoke(user_input)
        context = "\n".join(d.page_content[:300] for d in docs[:2])
        
        # Enhance prompt with disease awareness
        disease_list = ", ".join(medical_disease_data.keys())
        enhanced_prompt = system_prompt.format(
            context=context,
            input=user_input,
            disease_list=disease_list
        )
        
        raw_response = llm(enhanced_prompt, max_length=800)[0]['generated_text']
        final_response = enhance_response(raw_response, llm)
        
        return jsonify({"answer": final_response})
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "I'm having trouble answering that. Please try again or rephrase your question.",
            "debug": str(e) if app.debug else None
        }), 500
    
print(f"Current working directory: {os.getcwd()}")
print(f"Template folder path: {os.path.abspath(app.template_folder)}")
print(f"Static folder path: {os.path.abspath(app.static_folder)}")
print(f"chat.html exists: {os.path.exists(os.path.join(app.template_folder, 'chat.html'))}")


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

