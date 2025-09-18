#this file is app.py
from flask import Flask, render_template, jsonify, request, session
from src.helper import download_huggingface_embeddings, load_medical_disease_data
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from tqdm.auto import tqdm
import time
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.prompt import system_prompt, enhance_response
import os
from store_index import text_chunks
from transformers import pipeline 
import logging
from typing import Dict, Any, Optional, List
from googletrans import Translator
from datetime import timedelta
from collections import deque
from huggingface_hub import InferenceClient
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.prompts import PromptTemplate
import wave
import io
import base64
from datetime import datetime
import speech_recognition as sr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
conversation_memory = {}
MAX_HISTORY = 4

LANGUAGE_MAP = {
    'en': 'english',
    'zu': 'zulu',
    'xh': 'xhosa',
    'af': 'afrikaans',
    'st': 'sesotho',
    'tn': 'setswana',
    'ts': 'xitsonga',
    've': 'tshivenda',
    'ss': 'siswati',
    'nso': 'Northern Sotho',
    'nr': 'ndebele'
}

SUPPORTED_TRANSLATION_LANGS = ['en', 'zu', 'xh', 'af', 'st', 'tn']

# Initialize Pinecone
try:
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    print(f"✓ Successfully connected to Pinecone index '{index_name}'")
    
    retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    
except Exception as e:
    print(f"✗ Pinecone error: {str(e)}")
    print("Creating local FAISS store as fallback...")
    from langchain_community.vectorstores import FAISS
    
    # Create fallback FAISS store
    if os.path.exists("full_medical_knowbase"):
        docsearch = FAISS.load_local("full_medical_knowbase", embeddings)
    else:
        docsearch = FAISS.from_documents(text_chunks, embeddings)
        docsearch.save_local("full_medical_knowbase")
    
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

def analyze_symptoms(user_input: str, lang: str = "en") -> Dict:
    """Enhanced symptom analysis with better pattern matching"""
    context = {
        'symptoms': [],
        'locations': [],
        'activities': [],
        'contacts': [],
        'timeframe': None,
        'severity': None
    }
    
    input_lower = user_input.lower()
    
    symptom_keywords = {
        'fever': ['fever', 'temperature', 'hot', 'burning up'],
        'headache': ['headache', 'head hurts', 'head pain', 'head aching'],
        'muscle pain': ['muscle', 'body ache', 'muscles aching', 'body pain'],
        'fatigue': ['tired', 'weak', 'exhausted', 'fatigue', 'no energy'],
        'rash': ['rash', 'spots', 'skin marks', 'bumps'],
        'cough': ['cough', 'coughing'],
        'sore throat': ['throat', 'swallow hurts'],
        'diarrhea': ['diarrhea', 'loose stool', 'stomach runs'],
        'nausea': ['nausea', 'feel sick', 'vomit', 'throw up'],
    }
    
    for symptom, keywords in symptom_keywords.items():
        if any(kw in input_lower for kw in keywords):
            context['symptoms'].append(symptom)
    
    locations = ["durban", "johannesburg", "cape town", "pretoria", "limpopo", 
                "mpumalanga", "kwazulu-natal", "mozambique", "zimbabwe", "botswana"]
    for loc in locations:
        if loc in input_lower:
            context['locations'].append(loc)
    
    activity_patterns = {
        'sexual': ['unprotected sex', 'had sex', 'sexual', 'intercourse'],
        'travel': ['travel', 'trip', 'vacation', 'went to', 'visited'],
        'food': ['ate', 'eating', 'food', 'meal'],
        'mosquito': ['mosquito', 'bitten', 'bugs', 'insects']
    }
    
    for activity_type, patterns in activity_patterns.items():
        if any(p in input_lower for p in patterns):
            context['activities'].append(activity_type)
    
    possible_conditions = []
    
    for disease_name, disease_data in medical_disease_data.items():
        score = 0
        matched_symptoms = []
        matched_factors = []
        
        for symptom in context['symptoms']:
            if symptom in str(disease_data.get('symptoms', [])).lower():
                score += 3
                matched_symptoms.append(symptom)
        
        how_contracted = str(disease_data.get('how_contracted', [])).lower()
        if 'sexual' in context['activities'] and 'sexual' in how_contracted:
            score += 5
            matched_factors.append('sexual transmission')
        
        if 'travel' in context['activities']:
            high_risk_areas = str(disease_data.get('high_risk_areas', [])).lower()
            for loc in context['locations']:
                if loc in high_risk_areas:
                    score += 4
                    matched_factors.append(f'endemic in {loc}')
        
        if score > 0:
            confidence = min(score / 10, 1.0)
            
            possible_conditions.append({
                'disease': disease_name,
                'confidence': confidence,
                'score': score,
                'matched_symptoms': matched_symptoms,
                'matched_factors': matched_factors,
                'description': disease_data.get('description', ''),
                'treatment': disease_data.get('treatment', [])
            })
    
    possible_conditions.sort(key=lambda x: x['confidence'], reverse=True)
    
    urgency = 'low'
    urgent_symptoms = ['chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious']
    if any(s in input_lower for s in urgent_symptoms):
        urgency = 'high'
    elif len(context['symptoms']) >= 3 or 'fever' in context['symptoms']:
        urgency = 'moderate'
    
    return {
        'context': context,
        'possible_conditions': possible_conditions[:5],
        'urgency': urgency,
        'risk_factors': {
            'travel': 'travel' in context['activities'],
            'sexual': 'sexual' in context['activities']
        }
    }

def generate_follow_up_questions(symptoms: list, risk_factors: dict, context: dict = None) -> list:
    """Generate intelligent follow-up questions based on medical analysis"""
    
    questions = []
    
    if 'fever' in symptoms:
        questions.extend([
            "How high is your fever and how long have you had it?",
            "Are you experiencing chills, sweating, or shaking?"
        ])
    
    if 'headache' in symptoms:
        questions.extend([
            "How severe is the headache on a scale of 1-10?",
            "Is the headache different from your usual headaches?"
        ])
    
    if risk_factors.get('sexual'):
        questions.extend([
            "When was this exposure and have you been tested since?",
            "Are you experiencing any unusual discharge, sores, or burning sensation?"
        ])
    
    if risk_factors.get('travel'):
        questions.extend([
            "Which specific areas did you visit and when did you return?",
            "Did you take any preventive medications during travel?"
        ])
    
    questions.append("Do you have any chronic medical conditions or take regular medications?")
    
    seen = set()
    unique_questions = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique_questions.append(q)
    
    return unique_questions[:3]

voice_transcriptions = {}

def transcribe_audio_free(audio_data):
    """Transcribe audio using free speech recognition"""
    try:
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        
        audio_file = sr.AudioFile(io.BytesIO(audio_data))
        
        with audio_file as source:
            audio = recognizer.record(source)
        
        text = recognizer.recognize_google(audio)
        return text
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None

def summarize_conversation(messages: list) -> dict:
    """Summarize medical conversation and extract key points"""
    
    all_symptoms = set()
    medications_mentioned = []
    diagnoses_discussed = []
    recommendations = []
    
    for msg in messages:
        msg_lower = msg.lower()
        
        symptom_keywords = ['fever', 'headache', 'cough', 'pain', 'fatigue', 'nausea', 
                          'vomiting', 'diarrhea', 'rash', 'weakness', 'dizziness', 'chills',
                          'sweating', 'sore throat', 'runny nose', 'body ache', 'muscle pain',
                          'abdominal pain', 'shortness of breath', 'chest pain', 'bleeding',
                          'swelling', 'itching', 'redness', 'loss of appetite', 'weight loss',
                          'night sweats', 'confusion', 'seizures', 'loss of consciousness',
                          'joint pain', 'stiffness', 'numbness', 'tingling', 'vision changes',
                          'hearing loss', 'ear pain', 'toothache', 'back pain', 'leg pain']
        for symptom in symptom_keywords:
            if symptom in msg_lower:
                all_symptoms.add(symptom)
        
        med_keywords = ['paracetamol', 'ibuprofen', 'antibiotic', 'aspirin', 'insulin']
        for med in med_keywords:
            if med in msg_lower:
                medications_mentioned.append(med)
        
        diagnostic_terms = ['test', 'x-ray', 'blood test', 'scan', 'examination',
                            'diagnosis', 'diagnose', 'lab results']
        for term in diagnostic_terms:
            if term in msg_lower:
                diagnoses_discussed.append(term)
    
    summary = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_messages': len(messages),
        'symptoms_identified': list(all_symptoms),
        'medications_discussed': medications_mentioned,
        'diagnostic_procedures': diagnoses_discussed,
        'key_points': [],
        'doctor_recommendations': []
    }
    
    for i, msg in enumerate(messages):
        if 'urgent' in msg.lower() or 'emergency' in msg.lower():
            summary['key_points'].append(f"Urgent care mentioned at message {i+1}")
        if 'follow up' in msg.lower() or 'follow-up' in msg.lower():
            summary['key_points'].append(f"Follow-up care discussed at message {i+1}")
    
    if 'fever' in all_symptoms and 'headache' in all_symptoms:
        summary['doctor_recommendations'].append("Consider malaria testing if patient has travel history")
    if 'cough' in all_symptoms and 'fever' in all_symptoms:
        summary['doctor_recommendations'].append("Screen for TB if cough persists over 2 weeks")
    if len(all_symptoms) >= 3:
        summary['doctor_recommendations'].append("Multiple symptoms present - comprehensive assessment recommended")
    
    return summary

def format_medical_response(analysis: dict, user_input: str) -> str:
    """Format comprehensive medical response with South African context"""
    
    response_parts = []
    
    symptoms = analysis['context']['symptoms']
    if symptoms:
        response_parts.append(f"I understand you're experiencing {', '.join(symptoms)}. Let me help analyze what this might indicate.\n")
    
    conditions = analysis['possible_conditions']
    if conditions:
        response_parts.append("**Based on your symptoms, here are the most likely conditions:**\n")
        
        for i, condition in enumerate(conditions[:3], 1):
            confidence_text = "High likelihood" if condition['confidence'] > 0.7 else "Moderate possibility" if condition['confidence'] > 0.4 else "Possible"
            
            response_parts.append(f"\n**{i}. {condition['disease'].upper()}** ({confidence_text})")
            
            if condition.get('description'):
                response_parts.append(f"\n   {condition['description'][:200]}...")
            
            if condition.get('matched_symptoms'):
                response_parts.append(f"\n   • Matching symptoms: {', '.join(condition['matched_symptoms'])}")
            
            if condition.get('matched_factors'):
                response_parts.append(f"\n   • Risk factors: {', '.join(condition['matched_factors'])}")
            
            if condition.get('treatment') and len(condition['treatment']) > 0:
                response_parts.append(f"\n   • Initial step: {condition['treatment'][0]}")
    
    urgency = analysis.get('urgency', 'low')
    response_parts.append("\n")
    
    if urgency == 'high':
        response_parts.append("🚨 **URGENT**: These symptoms require immediate medical attention. Go to the nearest hospital or call 10177.")
    elif urgency == 'moderate':
        response_parts.append("⚠️ **IMPORTANT**: Please visit a clinic within 24 hours for proper evaluation and testing.")
    else:
        response_parts.append("💡 **RECOMMENDATION**: Schedule a clinic visit soon, especially if symptoms persist or worsen.")
    
    response_parts.append("\n\n---\n*This is preliminary guidance only. Please see a healthcare professional for proper diagnosis and treatment.*")
    
    return "\n".join(response_parts)

def get_south_africa_guidance(disease_info: Dict[str, Any]) -> str:
    """Generate South Africa-specific guidance for a disease."""
    name = disease_info.get('name', '').lower()
    
    guidance_map = {
        'hiv': "ART medications available at all public clinics. CD4 testing requires referral.",
        'aids': "Advanced care available at district hospitals. Support groups widely available.",
        'malnutrition': "Nutritional supplements at primary clinics. Severe cases to district hospitals.",
        'asthma': "Inhalers available at clinics. Emergency care at community health centers.",
        'gonorrhea': "Treatment available at all clinics. Partner notification services provided."
    }
    
    return guidance_map.get(name, 
        "Standard treatment available at primary healthcare clinics. Severe cases should be referred.")

def clean_response(response):
    """Remove auto-generated boilerplate from responses"""
    if not response:
        return ""
    
    unwanted_phrases = [
        "Improve the medical response for rural South African clinics:",
        "Rural clinic response:",
        "I'll help you",
        "Let me help you"
    ]
    
    for phrase in unwanted_phrases:
        response = response.replace(phrase, "")
    
    return response.strip()

def translate_text(text, target_lang='en'):
    if target_lang == 'en':
        return text
    
    try:
        translator = Translator(to_lang=target_lang)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        return text

class SimpleMedicalLLM:
    def __init__(self):
        self.name = "SimpleMedicalLLM"
    
    def invoke(self, input_dict):
        """Simple response generation without external models"""
        if isinstance(input_dict, dict):
            query = input_dict.get('input', '')
        else:
            query = str(input_dict)
        
        query_lower = query.lower()
        
        if 'hiv' in query_lower:
            return "HIV (Human Immunodeficiency Virus) attacks the immune system. Symptoms include fever, fatigue, swollen lymph nodes, and weight loss. Free HIV testing and ART treatment are available at all South African public clinics."
        
        if 'malaria' in query_lower:
            return "Malaria is transmitted by mosquito bites in endemic areas. Symptoms include high fever, chills, headache, and body aches. If you've traveled to malaria areas and have fever, seek immediate medical testing."
        
        if 'tb' in query_lower or 'tuberculosis' in query_lower:
            return "Tuberculosis (TB) affects the lungs primarily. Symptoms include persistent cough, night sweats, weight loss, and fever. TB testing and treatment are free at South African clinics."
        
        return "I recommend visiting your nearest clinic for proper medical evaluation. For emergencies, call 10177."
    
    def __call__(self, prompt, **kwargs):
        return self.invoke({'input': prompt})

try:
    client = InferenceClient(
        model="microsoft/BioGPT",
        token=os.getenv("HUGGINGFACE_API_TOKEN")
    )
    
    class HFWrapper:
        def __init__(self, client):
            self.client = client
        
        def invoke(self, input_dict):
            if isinstance(input_dict, dict):
                prompt = input_dict.get('input', '')
            else:
                prompt = str(input_dict)
            
            try:
                response = self.client.text_generation(
                    prompt,
                    max_new_tokens=300,
                    temperature=0.7
                )
                return response
            except:
                return SimpleMedicalLLM().invoke(input_dict)
    
    llm = HFWrapper(client)
    print("✓ Using Hugging Face API for responses")
    
except Exception as e:
    print(f"Note: Using simple response system. API error: {e}")
    llm = SimpleMedicalLLM()

doc_prompt = PromptTemplate(
    input_variables=["context", "input"],
    template="""You are EDI, a South African medical assistant. Use the context to answer the question.

Context: {context}

Question: {input}

Medical Response:"""
)

try:
    question_answer_chain = create_stuff_documents_chain(llm, doc_prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    print("✓ RAG chain created successfully")
except Exception as e:
    print(f"Note: RAG chain unavailable: {e}")
    rag_chain = None

app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.before_request
def track_conversation():
    session_id = request.headers.get('X-Session-ID', 'default')
    if session_id not in conversation_memory:
        conversation_memory[session_id] = deque(maxlen=MAX_HISTORY)

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or 'msg' not in data:
            return jsonify({"error": "Invalid request format"}), 400
        
        user_input = data.get("msg", "").strip()
        if not user_input:
            return jsonify({"error": "Empty message"}), 400
        
        session_id = data.get("session_id", "default")
        target_lang = data.get("lang", "en")
        
        if session_id not in conversation_memory:
            conversation_memory[session_id] = deque(maxlen=MAX_HISTORY)
        
        analysis = analyze_symptoms(user_input)
        
        direct_match = find_matching_disease(user_input)
        
        if direct_match:
            response = f"**{direct_match.get('name', 'Disease').upper()}**\n\n"
            response += f"{direct_match.get('description', '')}\n\n"
            
            if direct_match.get('symptoms'):
                response += f"**Symptoms:** {', '.join(direct_match['symptoms'])}\n\n"
            
            if direct_match.get('treatment'):
                response += f"**Treatment:** {direct_match['treatment'][0]}\n\n"
            
            response += "For more information or if you're experiencing these symptoms, please visit your nearest clinic."
        
        elif len(analysis['possible_conditions']) > 0:
            response = format_medical_response(analysis, user_input)
            
            if analysis['possible_conditions'][0]['confidence'] < 0.8:
                follow_ups = generate_follow_up_questions(
                    analysis['context']['symptoms'],
                    analysis['risk_factors'],
                    analysis['context']
                )
                if follow_ups:
                    response += "\n\n**To better assess your condition, could you tell me:**\n"
                    for i, q in enumerate(follow_ups, 1):
                        response += f"{i}. {q}\n"
        
        else:
            if rag_chain:
                try:
                    rag_response = rag_chain.invoke({"input": user_input})
                    response = clean_response(rag_response.get('answer', ''))
                except:
                    response = llm.invoke({'input': user_input})
            else:
                response = llm.invoke({'input': user_input})
            
            if len(response.split()) < 20:
                response = enhance_response(response, analysis['context'])
        
        if target_lang != "en" and target_lang in SUPPORTED_TRANSLATION_LANGS:
            response = translate_text(response, target_lang)
        
        conversation_memory[session_id].append((user_input, response))
        
        return jsonify({
            "answer": response,
            "session_id": session_id,
            "context": {
                "symptoms": analysis['context']['symptoms'],
                "conditions": [c['disease'] for c in analysis['possible_conditions'][:3]],
                "urgency": analysis['urgency']
            }
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({"answer": "I apologize, but I'm having trouble processing your request. Please try rephrasing your question or describe your symptoms in more detail."}), 200

@app.route("/record_audio", methods=["POST"])
def record_audio():
    """Handle audio recording from browser"""
    try:
        data = request.get_json()
        audio_data = data.get('audio')
        session_id = data.get('session_id', 'default')
        
        if not audio_data:
            return jsonify({"error": "No audio data received"}), 400
        
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        
        transcription = transcribe_audio_free(audio_bytes)
        
        if transcription:
            if session_id not in voice_transcriptions:
                voice_transcriptions[session_id] = []
            voice_transcriptions[session_id].append({
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'text': transcription,
                'speaker': 'patient'
            })
            
            analysis = analyze_symptoms(transcription)
            
            return jsonify({
                "transcription": transcription,
                "analysis": analysis,
                "success": True
            })
        else:
            return jsonify({
                "error": "Could not transcribe audio",
                "success": False
            })
            
    except Exception as e:
        logger.error(f"Audio recording error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/get_conversation_summary", methods=["POST"])
def get_conversation_summary():
    """Generate summary of the conversation for doctor"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        conversation = conversation_memory.get(session_id, [])
        
        voice_data = voice_transcriptions.get(session_id, [])
        
        all_messages = []
        for user_msg, ai_response in conversation:
            all_messages.append(user_msg)
            all_messages.append(ai_response)
        
        for voice in voice_data:
            all_messages.append(voice['text'])
        
        summary = summarize_conversation(all_messages)
        
        report = format_medical_report(summary, session_id)
        
        return jsonify({
            "summary": summary,
            "report": report,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def format_medical_report(summary: dict, session_id: str) -> str:
    """Format summary as a professional medical report"""
    
    report = []
    report.append("=" * 60)
    report.append("MEDICAL CONSULTATION SUMMARY")
    report.append("=" * 60)
    report.append("")
    report.append(f"Session ID: {session_id}")
    report.append(f"Date & Time: {summary['timestamp']}")
    report.append(f"Total Exchanges: {summary['total_messages']}")
    report.append("")
    
    if summary['symptoms_identified']:
        report.append("SYMPTOMS IDENTIFIED:")
        report.append("-" * 40)
        for symptom in summary['symptoms_identified']:
            report.append(f"• {symptom.capitalize()}")
        report.append("")
    
    if summary['medications_discussed']:
        report.append("MEDICATIONS DISCUSSED:")
        report.append("-" * 40)
        for med in summary['medications_discussed']:
            report.append(f"• {med.capitalize()}")
        report.append("")
    
    if summary['key_points']:
        report.append("KEY POINTS:")
        report.append("-" * 40)
        for point in summary['key_points']:
            report.append(f"• {point}")
        report.append("")
    
    if summary['doctor_recommendations']:
        report.append("AI RECOMMENDATIONS FOR DOCTOR:")
        report.append("-" * 40)
        for rec in summary['doctor_recommendations']:
            report.append(f"• {rec}")
        report.append("")
    
    report.append("=" * 60)
    report.append("NOTE: This is an AI-generated summary.")
    report.append("Please verify all information with the patient.")
    report.append("=" * 60)
    
    return "\n".join(report)

print("\n=== System Verification ===")
print(f"✓ Flask app initialized")
print(f"✓ Medical data loaded: {len(medical_disease_data)} diseases")
print(f"✓ Embeddings initialized")
print(f"✓ Server ready at http://localhost:5000")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

