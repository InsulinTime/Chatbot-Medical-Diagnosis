#this file is src/prompt.py
system_prompt = """You are EDI, an advanced South African medical assistant designed to help patients and healthcare providers. Your primary goals are:

**CORE RESPONSIBILITIES:**
1. Provide accurate, culturally-sensitive medical guidance
2. Analyze symptoms intelligently using available medical data
3. Ask relevant follow-up questions to gather critical information
4. Recognize urgency levels and guide patients appropriately
5. Support multiple South African languages with medical accuracy

**CONVERSATION STYLE:**
- Empathetic but professional (like a skilled clinic nurse)
- Use clear, simple language appropriate for diverse educational backgrounds
- Acknowledge patient concerns before providing analysis
- Ask targeted questions to narrow down possibilities
- Provide structured, actionable guidance

**MEDICAL ANALYSIS FRAMEWORK:**
When a patient describes symptoms:
1. ACKNOWLEDGE their concern with empathy
2. ANALYZE symptoms against your medical database
3. IDENTIFY potential conditions based on:
   - Symptom patterns
   - Geographic risk factors (travel, local diseases)
   - Exposure history (sexual, occupational, environmental)
   - Timeline and progression
4. ASK 2-3 specific follow-up questions to clarify
5. RECOMMEND appropriate next steps based on urgency

**CRITICAL PRIORITIES FOR SOUTH AFRICA:**
- HIV/AIDS awareness and testing guidance
- Tuberculosis screening and treatment
- Malaria in high-risk areas (Limpopo, Mpumalanga, KZN)
- Diabetes and hypertension management
- Maternal and child health

**URGENCY ASSESSMENT:**
HIGH URGENCY (immediate medical attention):
- Chest pain, difficulty breathing, severe bleeding
- Signs of meningitis (fever + headache + rash)
- Severe dehydration, high fever in children
- Suicidal thoughts or severe mental health crisis

MODERATE URGENCY (within 24-48 hours):
- Persistent fever, unexplained weight loss
- Possible STI symptoms after risky exposure
- Chronic symptoms worsening
- New onset of concerning symptoms

LOW URGENCY (routine clinic visit):
- Mild symptoms, health education requests
- Medication questions, prevention advice
- Follow-up on stable conditions

**LANGUAGE GUIDELINES:**
- Detect patient's preferred language from their input
- Provide key medical terms in both English and local language when appropriate
- Use culturally appropriate explanations and examples
- Respect traditional health beliefs while promoting evidence-based care

**RESPONSE STRUCTURE:**
1. Empathetic acknowledgment (1 sentence)
2. Medical analysis based on symptoms (2-3 sentences)
3. Relevant follow-up questions (2-3 questions maximum)
4. Clear next steps with urgency level
5. Important disclaimer about professional medical care

**EXAMPLE INTERACTION:**
Patient: "I have fever and headache after travelling to Mozambique"
EDI Response:
"I understand you're feeling unwell after your trip to Mozambique. Given your fever and headache following travel to a malaria-endemic area, this could indicate malaria, but other infections are also possible.

To help narrow this down:
1. When did your symptoms start in relation to your return?
2. Have you noticed any other symptoms like chills, sweating, or nausea?
3. Did you take malaria prevention medication during your trip?

RECOMMENDATION: This requires urgent evaluation within 24 hours at a clinic with malaria testing capability. Malaria can become serious quickly if untreated.

IMPORTANT: This is not a diagnosis. Please seek professional medical evaluation for proper testing and treatment."

**NEVER:**
- Provide definitive diagnoses
- Recommend specific medications without professional consultation
- Ignore or minimize serious symptoms
- Give medical advice beyond general guidance
- Contradict established medical guidelines

**ALWAYS:**
- Emphasize the need for professional medical evaluation
- Provide context about why certain conditions are considered
- Ask clarifying questions to better understand the situation
- Give clear guidance on urgency and next steps
- Maintain patient dignity and confidentiality"""

def enhance_response(response: str, context: dict = None) -> str:
    """Enhance responses with South African medical context"""
    
    # Check if response needs improvement
    if len(response.split()) < 15 or any(phrase in response.lower() for phrase in [
        "i don't know", "unclear", "cannot determine", "need more information"
    ]):
        
        # Add contextual medical guidance
        enhanced_parts = []
        
        if context and context.get('symptoms'):
            symptoms = context['symptoms']
            enhanced_parts.append(f"Based on the symptoms you've mentioned ({', '.join(symptoms)}), ")
            
            # Add condition-specific guidance
            if 'fever' in symptoms:
                enhanced_parts.append("fever can indicate various conditions from viral infections to more serious diseases like malaria or typhoid. ")
            
            if 'headache' in symptoms and 'fever' in symptoms:
                enhanced_parts.append("The combination of fever and headache requires careful evaluation, especially if you've traveled recently. ")
        
        # Add location-specific advice
        if context and context.get('locations'):
            locations = context['locations']
            for location in locations:
                if location.lower() in ['limpopo', 'mpumalanga', 'kwazulu-natal']:
                    enhanced_parts.append(f"Given your connection to {location}, malaria screening would be important. ")
                elif location.lower() in ['mozambique', 'zimbabwe', 'botswana']:
                    enhanced_parts.append(f"Travel to {location} increases risk for certain tropical diseases. ")
        
        # Add standard medical advice
        enhanced_parts.append("I recommend visiting your nearest clinic for proper evaluation. ")
        enhanced_parts.append("If symptoms are severe or worsening, seek immediate medical attention.")
        
        return ''.join(enhanced_parts)
    
    return response

def generate_follow_up_questions(symptoms: list, risk_factors: dict, context: dict = None) -> list:
    """Generate intelligent follow-up questions based on medical analysis"""
    
    questions = []
    
    # Symptom-specific questions
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
    
    if 'cough' in symptoms:
        questions.extend([
            "Are you coughing up any blood or colored sputum?",
            "How long have you had this cough?"
        ])
    
    # Risk factor specific questions
    if risk_factors.get('travel'):
        questions.extend([
            "Which countries did you visit and when did you return?",
            "Did you take any preventive medications during travel?",
            "Were you bitten by mosquitoes or other insects?"
        ])
    
    if risk_factors.get('sexual'):
        questions.extend([
            "When was this exposure and have you been tested since?",
            "Are you experiencing any unusual discharge or sores?"
        ])
    
    # General medical questions
    questions.extend([
        "Do you have any chronic medical conditions or take regular medications?",
        "Have you been in contact with anyone else who was sick?",
        "Are there any other symptoms you haven't mentioned?"
    ])
    
    # Return only the most relevant questions (max 3)
    return questions[:3]

def format_medical_response(analysis: dict, user_input: str) -> str:
    """Format comprehensive medical response"""
    
    response_parts = []
    
    # Empathetic acknowledgment
    symptoms = analysis.get('symptoms', [])
    if symptoms:
        response_parts.append(f"I understand you're experiencing {', '.join(symptoms)}. Let me help analyze what this might indicate.")
    else:
        response_parts.append("Thank you for sharing your health concerns with me.")
    
    # Medical analysis
    conditions = analysis.get('possible_conditions', [])
    if conditions:
        response_parts.append("\nBased on your symptoms and the information provided, here are some medical considerations:")
        
        for i, condition in enumerate(conditions[:3], 1):
            confidence = condition.get('confidence', 0)
            confidence_text = "high likelihood" if confidence > 0.7 else "moderate possibility" if confidence > 0.4 else "consideration"
            
            response_parts.append(f"\n{i}. **{condition['disease']}** - {confidence_text}")
            
            if condition.get('matched_symptoms'):
                response_parts.append(f"   Relevant symptoms: {', '.join(condition['matched_symptoms'])}")
            
            if condition.get('matched_locations'):
                response_parts.append(f"   Geographic factors: {', '.join(condition['matched_locations'])}")
    
    # Follow-up questions
    follow_ups = generate_follow_up_questions(
        symptoms, 
        analysis.get('risk_factors', {}),
        analysis.get('context', {})
    )
    
    if follow_ups:
        response_parts.append(f"\nTo provide better guidance, I need to ask:")
        for i, question in enumerate(follow_ups, 1):
            response_parts.append(f"{i}. {question}")
    
    # Urgency and recommendations
    urgency = analysis.get('urgency', 'low')
    if urgency == 'high':
        response_parts.append("\n🚨 **URGENT**: These symptoms require immediate medical attention. Please go to the nearest hospital or call emergency services.")
    elif urgency == 'moderate':
        response_parts.append("\n⚠️ **IMPORTANT**: Please visit a healthcare facility within the next 24 hours for evaluation.")
    else:
        response_parts.append("\n💡 **RECOMMENDATION**: Consider scheduling a clinic visit for proper evaluation, especially if symptoms persist or worsen.")
    
    # Medical disclaimer
    response_parts.append("\n---")
    response_parts.append("**MEDICAL DISCLAIMER**: This information is for educational purposes only and does not replace professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical concerns.")
    
    return "\n".join(response_parts)

def clean_response(response: str) -> str:
    """Clean and improve response quality"""
    
    unwanted_phrases = [
        "Improve the medical response for rural South African clinics:",
        "Rural clinic response:",
        "Based on the medical data provided:",
        "According to the information:"
    ]
    
    cleaned = response
    for phrase in unwanted_phrases:
        cleaned = cleaned.replace(phrase, "")
    
    lines = cleaned.split('\n')
    unique_lines = []
    for line in lines:
        if line.strip() and line not in unique_lines:
            unique_lines.append(line)
    
    cleaned = '\n'.join(unique_lines).strip()
    
    cleaned = cleaned.replace('\n\n\n', '\n\n')
    
    return cleaned

def create_receipt_content(conversation_history: list, patient_info: dict = None) -> str:
    """Generate formatted receipt for healthcare providers"""
    
    receipt_lines = []
    
    receipt_lines.extend([
        "=" * 60,
        "SOUTH AFRICAN HEALTH - MEDICAL PRE-SCREENING SUMMARY",
        "=" * 60,
        ""
    ])
    
    if patient_info:
        receipt_lines.extend([
            "PATIENT INFORMATION:",
            f"Session ID: {patient_info.get('session_id', 'N/A')}",
            f"Date & Time: {patient_info.get('timestamp', 'N/A')}",
            f"Language: {patient_info.get('language', 'English')}",
            ""
        ])
    
    receipt_lines.extend([
        "REPORTED SYMPTOMS & CONCERNS:",
        "-" * 40
    ])
    
    all_symptoms = set()
    risk_factors = set()
    key_statements = []
    
    for entry in conversation_history:
        if entry.get('user_input'):
            user_msg = entry['user_input']
            key_statements.append(f"• {user_msg}")
            
            common_symptoms = ['fever', 'headache', 'cough', 'pain', 'nausea', 'tired', 'weak']
            for symptom in common_symptoms:
                if symptom in user_msg.lower():
                    all_symptoms.add(symptom)
    
    if key_statements:
        receipt_lines.extend(key_statements)
        receipt_lines.append("")
    
    if all_symptoms:
        receipt_lines.extend([
            "IDENTIFIED SYMPTOMS:",
            ", ".join(sorted(all_symptoms)),
            ""
        ])
    
    receipt_lines.extend([
        "AI ANALYSIS SUMMARY:",
        "-" * 40,
        "• Pre-screening completed using EDI Medical AI",
        "• Analysis based on symptom patterns and risk factors",
        "• Recommendations provided for further evaluation",
        ""
    ])
    
    receipt_lines.extend([
        "RECOMMENDATIONS FOR HEALTHCARE PROVIDER:",
        "-" * 40,
        "• Review patient's travel history if applicable",
        "• Consider local disease prevalence (malaria, TB, HIV)",
        "• Assess urgency based on symptom progression",
        "• Verify and expand on AI-identified symptoms",
        ""
    ])
    
    receipt_lines.extend([
        "=" * 60,
        "IMPORTANT NOTES:",
        "• This is a pre-screening summary only",
        "• Not a substitute for professional medical assessment",
        "• AI analysis should support, not replace, clinical judgment",
        "",
        "For emergencies: 10177 (Ambulance) | 112 (Mobile Emergency)",
        "Generated by EDI Medical AI - South African Health System",
        "=" * 60
    ])
    
    return "\n".join(receipt_lines)