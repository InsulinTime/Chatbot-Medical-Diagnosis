from flask import Flask, render_template, jsonify, request, session
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
from typing import Dict, Any, Optional, List
from googletrans import Translator
from datetime import timedelta

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

def analyze_symptoms(user_input: str, lang: str = "en") -> Dict:
    """Analyze symptoms using medical data and patient context"""
    context = {
        'symptoms': [],
        'locations': [],
        'activities': [],
        'contacts': []
    }
    
    input_lower = user_input.lower()
    for disease in medical_disease_data['diseases']:
        for symptom in disease['symptoms']:
            if symptom.lower() in input_lower:
                context['symptoms'].append(symptom)
    
    for loc in ["durban", "cote d'ivoire", "botswana", "Zimbabwe", "Nigeria", "Ghana", "Tanzania",
                 "Guinea", "Liberia", "Sierra Leone", "the Democratic Republic of Congo", "Uganda",
                   "Ethiopia", "Kenya", "South Africa", "Mozambique", "Angola", "Namibia", "Zambia",
                    "Burundi", "Rwanda", "South Sudan", "Argentina", "Paraguay", "Columbia", "Brazil",
                     "India", "Pakistan", "Bangladash", "French Guiana", "Guyana", "Suriname", "Venezuela",
                       "Peru", "Bolivia", "Ecuador", "El Salvador", "Mexico", "Peru", "Belize", "Costa Rica",
                         "Honduras", "Nicaragua", "Panama", "Limpopo", "Mpumalanga", "KwaZulu-Natal", "North West",
                            "Angola", "Somalia", "Malawi" ]:
        if loc in input_lower:
            context['locations'].append(loc)
    
    risk_activities = ["unprotected sex", "mosquito bite", "needle sharing", "contact with contaminated water", "eating raw meat", 
                       "contact with infected person", "travel and exposed to high-risk area", "poor sanitation", "close contact with certain animals",
                        "Sharing Utensils and Cups", "bug bites", "drinking untreated water", "exposured to contaminated surfaces"]
    for activity in risk_activities:
        if activity in input_lower:
            context['activities'].append(activity)
    
    possible_conditions = []
    for disease in medical_disease_data['diseases']:
        score = 0
        
        symptom_matches = sum(1 for s in disease['symptoms'] 
                          if any(s.lower() in inp for inp in [input_lower, *context['symptoms']]))
        
        location_matches = any(loc.lower() in disease.get('high_risk_areas', []) 
                           for loc in context['locations'])
        
        activity_matches = any(act.lower() in ' '.join(disease.get('how_contracted', []))
                           for act in context['activities'])
        
        score = (symptom_matches * 3) + (location_matches * 2) + activity_matches
        
        if score > 0:
            possible_conditions.append({
                'disease': disease['name'],
                'score': score,
                'matched_symptoms': [s for s in disease['symptoms'] 
                                  if any(s.lower() in inp for inp in [input_lower, *context['symptoms']])],
                'matched_activities': [a for a in disease.get('how_contracted', [])
                                     if any(a.lower().contains(act) for act in context['activities'])],
                'matched_locations': [loc for loc in disease.get('high_risk_areas', [])
                                    if any(loc.lower() == l.lower() for l in context['locations'])]
            })
    
    possible_conditions.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'context': context,
        'possible_conditions': possible_conditions[:3]
    }

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

def format_diagnostic_response(analysis: Dict, context: str, lang: str) -> str:
    """Format the diagnostic results for the patient"""
    conditions = analysis['possible_conditions']
    
    if not conditions:
        return "I couldn't determine possible conditions. Please consult a doctor."
    
    response = [
        "Based on your symptoms and history, possible conditions include:",
        ""
    ]
    
    for cond in conditions:
        disease_info = next((d for d in medical_disease_data['diseases'] 
                           if d['name'] == cond['disease']), None)
        if not disease_info:
            continue
            
        response.extend([
            f"• {cond['disease']} (Probability: {cond['score']}/10)",
            f"  - Matching symptoms: {', '.join(cond['matched_symptoms'])}",
            f"  - Possible causes: {', '.join(cond['matched_activities'])}",
            f"  - Recommended action: {disease_info['treatment'][0] if disease_info['treatment'] else 'Consult doctor'}",
            ""
        ])
    
    response.extend([
        "Additional information from medical sources:",
        context,
        "",
        "This is not a diagnosis. Please see a healthcare professional for confirmation."
    ])
    
    return "\n".join(response)

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

def clean_response(response):
    """Remove auto-generated boilerplate from responses"""
    unwanted_phrases = [
        "Improve the medical response for rural South African clinics:",
        "Rural clinic response:"
    ]
    for phrase in unwanted_phrases:
        response = response.replace(phrase, "")
    return response.strip()
    
def translate_text(text, target_lang='en'):
    if target_lang == 'en':
        return text
        
    try:
        clean_text = clean_response(text)
        
        medical_phrases = {
            'en': "HIV symptoms include",
            'af': "MIV simptome sluit in",
            'zu': "Izimpawu ze-HIV zihlanganisa",
            'xh': "Iimpawu ze-HIV ziquka",
            'tn': "Matlhago a HIV a akaretsa"
        }
        
        for en_phrase, trans_phrase in medical_phrases.items():
            if en_phrase in clean_text:
                return clean_text.replace(en_phrase, trans_phrase)
                
        translator = Translator(to_lang=target_lang)
        translated = translator.translate(clean_text)
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        return f"{clean_text}\n(Translation unavailable in {target_lang})"
    
def get_translated_error(lang, error_details=""):
    """Get error message in appropriate language"""
    error_messages = {
        'en': "I'm having trouble answering that. Please try again or rephrase your question.",
        'zu': "Ngiyaxhuzula ukuphendula lokho. Ngicela uzame futhi noma uchaze umbuzo wakho ngendlela ehlukile.",
        'xh': "Ndiyabandezelwa ukuphendula loo nto. Nceda uzame kwakhona okanye uphinde ufake umbuzo wakho ngolunye uhlobo.",
        'af': "Ek het probleme om dit te beantwoord. Probeer asseblief weer of herformuleer jou vraag.",
        'st': "Ke na le bothata ho araba seo. Ka kopo leka hape kapa hlalosa potso ea hao ka tsela e fapaneng.",
        'tn': "Ke na le mathata a go araba seo. Tsweetswee leka gape kgotsa buisa potso ya gago ka tsela e nngwe."
    }
    return error_messages.get(lang, error_messages['en']) + (
        f"\n(Technical details: {error_details}" if app.debug else "")


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

def generate_followups(patient_input: str, chat_history: List[str]) -> str:
    """Generate clinical follow-up questions based on conversation"""
    prompt = f"""As a clinician, what are 5 most important follow-up questions for:
Patient: {patient_input}
History: {chat_history[-2:] if chat_history else "None"}

Respond in this format:
1. [Priority 1 question]
2. [Priority 2 question]
3. [Priority 3 question]
4. [Priority 4 question]
5. [Priority 5 question]"""
    
    questions = llm(prompt, max_length=200)[0]['generated_text']
    return [q.split(".")[1].strip() for q in questions.split("\n") if q]

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

@app.route("/analyze_symptoms", methods=["POST"])
def analyze_symptoms():
    try:
        data = request.get_json()
        symptoms = {
            'main': data.get('main_symptom'),
            'duration': data.get('duration'),
            'severity': data.get('severity'),
            'additional': data.get('additional_symptoms')
        }
        target_lang = data.get('lang', 'en')
        
        analysis = analyze_symptom_patterns(symptoms)
        
        if target_lang != 'en':
            analysis = translate_text(analysis, target_lang)
        
        return jsonify({"analysis": analysis})
        
    except Exception as e:
        logger.error(f"Symptom analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def analyze_symptom_patterns(symptoms):
    """Basic symptom analysis - expand with your medical knowledge"""
    main = symptoms['main'].lower()
    additional = symptoms['additional'].lower()
    
    if 'fever' in main:
        if 'difficulty breathing' in additional:
            return ("Possible respiratory infection or malaria. "
                   "If fever is high (>39°C) or lasts more than 3 days, "
                   "please visit a clinic immediately.")
        return "Possible viral infection. Rest and drink fluids. If symptoms worsen, see a doctor."
    
    elif 'headache' in main:
        if 'dizziness' in additional:
            return "Possible migraine or blood pressure issue. Monitor symptoms and consult a doctor if severe."
        return "Common headache. Rest and hydrate. If persistent, consider medical advice."
    
    elif 'stomach pain' in main:
        if 'diarrhea' in additional or 'nausea' in additional:
            return "Possible food poisoning or gastrointestinal infection. Drink plenty of fluids and rest."
        return "Abdominal pain could have various causes. If severe or persistent, seek medical attention."
    
    return ("Based on your symptoms, it's recommended to monitor your condition. "
           "If symptoms persist or worsen, please consult a healthcare professional.")
    
@app.route("/get", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or 'msg' not in data:
            return jsonify({"error": "Invalid request format"}), 400
            
        user_input = data.get("msg", "").strip()
        if not user_input:
            return jsonify({"error": "Empty message"}), 400
        
        target_lang = data.get("lang", "en")
        
        if target_lang not in LANGUAGE_MAP:
            target_lang = 'en'
        
        lang_name = LANGUAGE_MAP.get(target_lang, 'english')
        logger.info(f"Processing request in {lang_name} (code: {target_lang})")
        
        processed_input = user_input
        if target_lang != "en":
            processed_input = translate_text(user_input, 'en', target_lang)
            logger.debug(f"Translated input: {user_input} -> {processed_input}")
        
        disease_info = find_matching_disease(processed_input)
        if disease_info:
            docs = retriever.invoke(disease_info['name'])[:1]
            rag_context = docs[0].page_content[:300] if docs else ""
            
            english_response = format_disease_response(disease_info, rag_context)
            
            if target_lang != "en":
                try:
                    translated_response = translate_text(english_response, target_lang)
                    return jsonify({"answer": translated_response})
                except Exception as e:
                    logger.error(f"Response translation error: {str(e)}")
                    return jsonify({
                        "answer": f"(Translation not available) {english_response}",
                        "warning": f"Full translation to {LANGUAGE_MAP[target_lang]} not available"
                    })
            return jsonify({"answer": english_response})
        
        analysis = analyze_symptoms(processed_input, target_lang)
        
        if should_ask_followup(processed_input) and not analysis.get('high_confidence_match', False):
            followups = generate_followups(processed_input, session.get('chat_history', []))
            if followups:
                return jsonify({
                    "action": "ask_followup",
                    "questions": followups[:2]
                })
        
        top_conditions = [cond['disease'] for cond in analysis['possible_conditions']]
        context = ""
        for condition in top_conditions:
            docs = retriever.invoke(condition)[:1]
            if docs:
                context += f"\n\n{condition}:\n{docs[0].page_content[:300]}"
        
        if analysis['possible_conditions']:
            english_response = format_diagnostic_response(analysis, context, target_lang)
        else:
            docs = retriever.invoke(processed_input)
            context = "\n".join(d.page_content[:300] for d in docs[:2])
            disease_list = ", ".join(medical_disease_data.keys())
            enhanced_prompt = system_prompt.format(
                context=context,
                input=processed_input,
                disease_list=disease_list
            )
            raw_response = llm(enhanced_prompt, max_length=800)[0]['generated_text']
            english_response = enhance_response(raw_response, llm)
        
        if target_lang != "en":
            try:
                translated_response = translate_text(english_response, target_lang)
                final_response = translated_response
            except Exception as e:
                logger.error(f"Failed to translate response to {target_lang}: {str(e)}")
                final_response = f"(Translation not available) {english_response}"
        else:
            final_response = english_response
        
        return jsonify({"answer": final_response})
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        error_msg = get_translated_error(target_lang, str(e))
        return jsonify({"error": error_msg}), 500
    
def should_ask_followup(text: str) -> bool:
    """Determine if the input seems like incomplete symptoms"""
    indicators = [
        "i have", "i feel", "i'm experiencing",
        "ndine", "ngizizwa", "ke na le"
    ]
    return any(indicator in text.lower() for indicator in indicators)

def get_translated_error(lang, error_details=""):
    """Get error message in appropriate language"""
    error_messages = {
        'en': "I'm having trouble answering that. Please try again or rephrase your question.",
        'zu': "Ngiyaxhuzula ukuphendula lokho. Ngicela uzame futhi noma uchaze umbuzo wakho ngendlela ehlukile.",
        'xh': "Ndiyabandezelwa ukuphendula loo nto. Nceda uzame kwakhona okanye uphinde ufake umbuzo wakho ngolunye uhlobo.",
        'af': "Ek het probleme om dit te beantwoord. Probeer asseblief weer of herformuleer jou vraag.",
        'st': "Ke na le bothata ho araba seo. Ka kopo leka hape kapa hlalosa potso ea hao ka tsela e fapaneng.",
        'tn': "Ke na le mathata a go araba seo. Tsweetswee leka gape kgotsa buisa potso ya gago ka tsela e nngwe."
    }
    
    # Default to English if language not supported
    return error_messages.get(lang, error_messages['en']) + (
        f"\n(Technical details: {error_details}" if app.debug else "")
    
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

