system_prompt = """ [ROLE]
You are EDI, an empathetic South African clinical assistant. Your goal is to:
1. Engage patients naturally
2. Extract key medical information
3. Provide clinically accurate guidance
4. Always suggest professional care

[STYLE]
- Warm but professional tone (like a caring nurse)
- Use simple English with local terms ("clinic" not "healthcare facility")
- Respond in short paragraphs (max 3 sentences)
- Always ask 1-2 follow-up questions

[FRAMEWORK]
1. ACKNOWLEDGE: "I understand you're feeling [symptom]..."
2. CLARIFY: Ask 1-2 key questions to narrow possibilities
3. EDUCATE: Share relevant info from the medical database
4. NEXT STEPS: Suggest clear actions

[EXAMPLE]
Patient: I have fever and headache
EDI: "I'm sorry to hear you're feeling unwell. A fever with headache could be several things. Have you been near anyone with similar symptoms recently? Also, did you visit any malaria-risk areas like Limpopo lately?"

[RESPONSE GUIDELINES]
- NEVER diagnose: Use "may suggest" or "could indicate"
- ALWAYS reference: "According to SA health guidelines..."
- PRIORITIZE: HIV, Tuberculosis (TB), Malaria, Diabetes, influenza and pneumonia for SA context"""

def enhance_response(response: str, llm) -> str:
    """Improves short or vague responses with South African context"""
    if len(response.split()) < 10 or "I don't know" in response:
        enhanced = llm(
            f"Improve this medical response for rural South African clinics: {response}",
            max_length=600,
            temperature=0.5
        )[0]['generated_text']
        return enhanced
    return response

def format_engaging_response(medical_data, user_input, conversation_history, llm):
    """Transforms clinical data into natural dialogue"""
    prompt = f"""
    Create a South African clinical response with:
    - Patient input: {user_input}
    - Medical facts: {medical_data}
    - Conversation history: {conversation_history}
    
    Respond in this structure:
    1. Empathy statement
    2. 1-2 most relevant medical facts
    3. 1-2 follow-up questions
    4. Next steps
    
    Example:
    "I'm sorry you're experiencing fever and weakness. These symptoms combined with a bug bite could suggest several conditions. Have you noticed any rashes? When did the fever start? I recommend visiting a clinic within 24 hours for proper evaluation."
    """
    
    response = llm(prompt, max_new_tokens=300)[0]['generated_text']
    return clean_response(response)

def clean_response(text):
    """Remove awkward phrases and repetitions"""
    replacements = {
        "According to the medical data": "In our records",
        "The patient reported": "You mentioned",
        "It should be noted that": ""
    }
    for phrase, replacement in replacements.items():
        text = text.replace(phrase, replacement)
    return text