document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatBox = document.getElementById('chatBox');
    const closeChat = document.getElementById('closeChat');
    const optionsModal = document.getElementById('optionsModal');
    const addExtra = document.getElementById('addExtra');
    const modalClose = document.querySelector('.modal-close-button');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const voiceBtn = document.getElementById('voiceBtn');
    const emergencyModal = document.getElementById('emergencyModal');
    const emergencyBtn = document.getElementById('emergencyHelp');
    const closeEmergency = document.getElementById('closeEmergency');
    const printBtn = document.getElementById('printBtn');
    const chatMessages = document.getElementById('chatMessages');
    
    const isSpeechRecognitionSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    let currentLanguage = 'en';
    let recognition;
    let currentSymptomStep = 0;
    let symptomResponses = {};
    const symptomQuestions = {
        en: [
            {
                question: "What is your main symptom?",
                options: ["Fever", "Headache", "Stomach pain", "Cough", "Rash"]
            },
            {
                question: "How long have you had this symptom?",
                options: ["Less than 24 hours", "1-3 days", "4-7 days", "More than 1 week"]
            },
            {
                question: "How severe is your symptom?",
                options: ["Mild (doesn't interfere with daily activities)", 
                        "Moderate (some interference)", 
                        "Severe (can't perform daily activities)"]
            },
            {
                question: "Do you have any of these additional symptoms?",
                options: ["Nausea/Vomiting", "Diarrhea", "Difficulty breathing", 
                        "Dizziness", "None of these"]
            }
        ],
        zu: [
            // Zulu translations of the same questions
            {
                question: "Yini isibonakaliso sakho esiyinhloko?",
                options: ["Ukushisa", "Isicanucanu", "Ubuhlungu besisu", "Ukukhwehlela", "I-rash"]
            },
            {
                question: "Usulokhu unalesi sifo isikhathi esingakanani?",
                options: ["Ngaphansi kwamahora angama-24", "Izinsuku eziyi-1-3", "Izinsuku ezi-4-7", "Ngaphezu kwesonto elilodwa"]
            },
            {
                question: "Ingabe isimo sakho sibi kangakanani?",
                options: ["Kancane (akuphazamisi imisebenzi yansuku zonke)", 
                        "Okulingene (kuphazamiseka okuthile)", 
                        "Kukhulu (akukwazi ukwenza imisebenzi yansuku zonke)"]
            },
            {
                question: "Ingabe unalezi zimpawu ezengeziwe?",
                options: ["Ukuhlanza/Ukudlikiza", "Ukuhuda", "Ubunzima bokuphefumula", 
                        "Ukudideka", "Akukho kulezi"]
            }
        ],
        xh: [
            // Xhosa translations
            {
                question: "Yintoni isifo sakho esiphambili?",
                options: ["Ukushisa", "Intlungu yentloko", "Intlungu yesisu", "Ukukhwehlela", "I-rash"]
            },
            {
                question: "Ube nesifo esi kangakanani ixesha?",
                options: ["Ngaphantsi kweeyure ezingama-24", "Iintsuku ezi-1-3", "Iintsuku ezi-4-7", "Ngaphezulu kwesonto"]
            },
            {
                question: "Ingabe isimo sakho sibi kangakanani?",
                options: ["Kancinci (akuphazamisi imisebenzi yemihla ngemihla)", 
                        "Okulingene (kuphazamisa okuthile)", 
                        "Kukhulu (akukwazi ukwenza imisebenzi yemihla ngemihla)"]
            },
            {
                question: "Ingabe unalezi zimpawu ezengeziwe?",
                options: ["Ukuhlanza/Ukudlikiza", "Ukuhuda", "Ubunzima bokuphefumula", 
                        "Ukudideka", "Akukho kulezi"]
            }
        ],
        af: [
            // Afrikaans translations
            {
                question: "Wat is jou hoofsimptoom?",
                options: ["Koors", "Hoofpyn", "Maagpyn", "Hoes", "Uitslag"]
            },
            {
                question: "Hoe lank het jy hierdie simptoom al?",
                options: ["Minder as 24 uur", "1-3 dae", "4-7 dae", "Meer as 'n week"]
            },
            {
                question: "Hoe ernstig is jou simptoom?",
                options: ["Lig (steur nie daaglikse aktiwiteite nie)", 
                        "Matig (steur sommige aktiwiteite)", 
                        "Ernstig (kan daaglikse aktiwiteite nie doen)"]
            },
            {
                question: "Het jy enige van hierdie bykomende simptome?",
                options: ["Nood/Braking", "Diarree", "Moeilikheid om asem te haal", 
                        "Duimel", "Geen van hierdie"]
            }
        ],
        st: [
            // Sesotho translations
            {
                question: "Ke eng letšoao la hau le ka sehloohong?",
                options: ["Feberu", "Hlooho e bohloko", "Bohloko ba mpa", "Ho khathala", "Rash"]
            },
            {
                question: "O bile le letšoao lena nako e kae?",
                options: ["Ka tlase ho lihora tse 24", "Matšatši a 1-3", "Matšatši a 4-7", "Ho feta beke"]
            },
            {
                question: "Boemo ba hau bo boima hakae?",
                options: ["Bonyane (ha bo phahamise mesebetsi ea letsatsi le letsatsi)", 
                        "Boemo bo boima (bo phahamisang mesebetsi e meng)", 
                        "Boima haholo (ha o khone ho etsa mesebetsi ea letsatsi le letsatsi)"]
            },
            {
                question: "Na u na le letšoao le leng?",
                options: ["Ho hlatsa/Ho hlatsa", "Ho hlatsa", "Mathata a ho hema", 
                        "Ho hloka matla", "Ha ho letho lena"]
            }
        ],
        tn: [
            // Setswana translations
            {
                question: "Ke eng letshwanelo la gago le lekgolo?",
                options: ["Feberu", "Hlooho e bohloko", "Bohloko jwa mpa", "Ho khathala", "Rash"]
            },
            {
                question: "O bile le letshwanelo le lengwe nako e kae?",
                options: ["Ka tlase ga diura tse 24", "Matšatši a 1-3", "Matšatši a 4-7", "Go feta beke"]
            },
            {
                question: "Boemo jwa gago bo boima jang?",
                options: ["Bonyane (ga bo phahamise mesebetsi ya letsatsi le letsatsi)", 
                        "Boemo bo boima (bo phahamisang mesebetsi e meng)", 
                        "Boima thata (ga o kgone go dira mesebetsi ya letsatsi le letsatsi)"]
            },
            {
                question: "Na o na le letshwanelo le lengwe?",
                options: ["Ho hlatsa/Ho hlatsa", "Ho hlatsa", "Mathata a ho hema", 
                        "Ho hloka matla", "Ha ho letho lena"]
            }
        ],
        ts: [
            // Tsonga translations
            {
                question: "I yini xiphemu xa wena lexi nga riki na xiphemu?",
                options: ["Ku hisa ka miri", "Ku pandza ka nhloko", "Ku vava ka khwiri", "Ku khohlola", "Ku vava"]
            },
            {
                question: "U bile ni xiphemu lexi nkarhi wo ka yini?",
                options: ["Hi ku tlula 24 hours", "1-3 days", "4-7 days", "Hi ku tlula 1 week"]
            },
            {
                question: "Xiphemu xa wena xi boima njhani?",
                options: ["Kancane (a xi khathalisi ntirho wa siku na siku)", 
                        "Kakhulu (xi khathalisa ntirho wo karhi)", 
                        "Kakhulu swinene (a u nga koti ku endla ntirho wa siku na siku)"]
            },
            {
                question: "U na ni xiphemu lexi engetelekeke?",
                options: ["Ku pfimba/Ku hlanta", "Ku pfimba ka khwiri", "Ku tika ku hefemula", 
                        "Ku pfimba ka nhloko", "Ku hava na xin'we xa leswi"]
            }
        ],
        ve: [
            // Venda translations
            {
                question: "ndi tshifhio tshiga tshanu tshihulwane?",
                options: ["Mufhiso", "U rema thoho", "U vhavha thumbuni", "U hoṱola", "Rash"]
            },
            {
                question: "U na na tshifhio tshiga tshanu tshihulwane?",
                options: ["Hu si na 24 hours", "1-3 days", "4-7 days", "Hu si na 1 week"]
            },
            {
                question: "Tshifhio tshiga tshanu tshi boima hani?",
                options: ["Vhuthu (a zwi khathaleli mvelele ya vhutshilo ha siku na siku)", 
                        "Vhuthu (zwi khathaleli mvelele ya vhutshilo ha siku na siku)", 
                        "Vhuthu vhukuma (a u nga kona u ita mvelele ya vhutshilo ha siku na siku)"]
            },
            {
                question: "U na na tshifhio tshiga tshanu tshi engetelelaho?",
                options: ["U pfimba/U hlanta", "U pfimba ka thumbuni", "U vha na mathata a u hema", 
                        "U vha na mathata a u vhala", "A hu na tshifhio tshiṅwe"]
            }
        ],
        ss: [
            // Swati translations
            {
                question: "Luyini luphawu lwakho loluyinhloko?",
                options: ["Imkhuhlane", "Kuphatfwa yinhloko", "Kuphatfwa sisu", "Kukhwehlela", "Umkhuhlane"]
            },
            {
                question: "Sewube naloluphawu sikhatsi lesingakanani?",
                options: ["Ngaphansi kwemahora langu-24", "Emalanga langu-1-3", "Emalanga langu-4-7", "Ngetulu kweliviki linye"]
            },
            {
                question: "Luhlobo luni loluphawu lwakho?",
                options: ["Luncane (aluphazamisi imisebenzi yelanga lelilodwa)", 
                        "Lukhulu (luphazamisa imisebenzi ethile)", 
                        "Lukhulu kakhulu (awukwazi ukwenza imisebenzi yelanga lelilodwa)"]
            },
            {
                question: "Unaluphi na lolu phawu olungeziwe?",
                options: ["Ukugula/Ukudlikiza", "Ukuhuda", "Ubunzima bokuphefumula", 
                        "Ukudideka", "Akukho kulezi"]
            }
        ],
        nso : [
            // Northern Sotho translations
            {
                question: "Ke eng letšatši la gago le lekgolo?",
                options: ["Feberu", "Hlooho e bohloko", "Bohloko ba mpa", "Ho khathala", "Rash"]
            },
            {
                question: "O bile le letšatši le lengwe nako e kae?",
                options: ["Ka tlase ga diura tse 24", "Matšatši a 1-3", "Matšatši a 4-7", "Ho feta beke"]
            },
            {
                question: "Boemo ba gago bo boima hakae?",
                options: ["Bonyane (ga bo phahamise mesebetsi ya letsatsi le letsatsi)", 
                        "Boemo bo boima (bo phahamisang mesebetsi e meng)", 
                        "Boima haholo (ga o kgone go dira mesebetsi ya letsatsi le letsatsi)"]
            },
            {
                question: "Na o na le letšatši le lengwe?",
                options: ["Ho hlatsa/Ho hlatsa", "Ho hlatsa", "Mathata a ho hema", 
                        "Ho hloka matla", "Ha ho letho lena"]
            }    
        ],
        nr: [
            // Ndebele translations
            {
                question: "Yini isibonakaliso sakho esiyinhloko?",
                options: ["Ukushisa", "Isicanucanu", "Ubuhlungu besisu", "Ukukhwehlela", "I-rash"]
            },
            {
                question: "Usulokhu unalesi sifo isikhathi esingakanani?",
                options: ["Ngaphansi kwamahora angama-24", "Izinsuku eziyi-1-3", "Izinsuku ezi-4-7", "Ngaphezu kwesonto elilodwa"]
            },
            {
                question: "Ingabe isimo sakho sibi kangakanani?",
                options: ["Kancane (akuphazamisi imisebenzi yansuku zonke)", 
                        "Okulingene (kuphazamiseka okuthile)", 
                        "Kukhulu (akukwazi ukwenza imisebenzi yansuku zonke)"]
            },
            {
                question: "Ingabe unalezi zimpawu ezengeziwe?",
                options: ["Ukuhlanza/Ukudlikiza", "Ukuhuda", "Ubunzima bokuphefumula", 
                        "Ukudideka", "Akukho kulezi"]
            }
        ]
    };

    // Add these event listeners
    document.getElementById('symptomCheck').addEventListener('click', function() {
        optionsModal.classList.remove('active');
        startSymptomChecker();
    });

    document.getElementById('prevSymptom').addEventListener('click', prevSymptomStep);
    document.getElementById('nextSymptom').addEventListener('click', nextSymptomStep);

    // Add these functions
    function startSymptomChecker() {
        currentSymptomStep = 0;
        symptomResponses = {};
        document.getElementById('symptomCheckerModal').classList.add('active');
        renderSymptomStep();
    }

    function renderSymptomStep() {
        const stepsContainer = document.getElementById('symptomSteps');
        stepsContainer.innerHTML = '';
        
        const questions = symptomQuestions[currentLanguage] || symptomQuestions.en;
        
        // Add progress bar
        const progressPercent = (currentSymptomStep / (questions.length - 1)) * 100;
        stepsContainer.innerHTML = `
            <div class="symptom-progress">
                <div class="symptom-progress-bar" style="width: ${progressPercent}%"></div>
            </div>
        `;
        
        questions.forEach((q, index) => {
            const stepDiv = document.createElement('div');
            stepDiv.className = `symptom-step ${index === currentSymptomStep ? 'active' : ''}`;
            stepDiv.innerHTML = `
                <div class="symptom-question">${q.question}</div>
                <div class="symptom-options">
                    ${q.options.map(opt => `
                        <div class="symptom-option" data-value="${opt}">${opt}</div>
                    `).join('')}
                </div>
            `;
            stepsContainer.appendChild(stepDiv);
            
            // Select previously chosen option if exists
            if (symptomResponses[index]) {
                const options = stepDiv.querySelectorAll('.symptom-option');
                options.forEach(opt => {
                    if (opt.dataset.value === symptomResponses[index]) {
                        opt.classList.add('selected');
                    }
                });
            }
        });
        
        // Set up option selection
        document.querySelectorAll('.symptom-option').forEach(option => {
            option.addEventListener('click', function() {
                this.parentNode.querySelectorAll('.symptom-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                this.classList.add('selected');
                symptomResponses[currentSymptomStep] = this.dataset.value;
            });
        });
        
        // Update nav buttons
        document.getElementById('prevSymptom').disabled = currentSymptomStep === 0;
        document.getElementById('nextSymptom').textContent = 
            currentSymptomStep === questions.length - 1 ? 
            (currentLanguage === 'en' ? 'Finish' : 
            currentLanguage === 'zu' ? 'Qeda' : 
            currentLanguage === 'xh' ? 'Gqiba' : 'Voltooi') : 
            (currentLanguage === 'en' ? 'Next' : 
            currentLanguage === 'zu' ? 'Okulandelayo' : 
            currentLanguage === 'xh' ? 'Okulandelayo' : 'Volgende');
    }

    function prevSymptomStep() {
        if (currentSymptomStep > 0) {
            currentSymptomStep--;
            renderSymptomStep();
        }
    }

    function nextSymptomStep() {
        const questions = symptomQuestions[currentLanguage] || symptomQuestions.en;
        
        if (!symptomResponses[currentSymptomStep]) {
            alert(currentLanguage === 'en' ? 'Please select an option' : 
                currentLanguage === 'zu' ? 'Sicela ukhethe inketho' :
                currentLanguage === 'xh' ? 'Nceda khetha inketho' :
                'Kies asseblief \'n opsie');
            return;
        }
        
        if (currentSymptomStep < questions.length - 1) {
            currentSymptomStep++;
            renderSymptomStep();
        } else {
            // Submit symptoms for analysis
            submitSymptoms();
        }
    }

    async function submitSymptoms() {
        document.getElementById('symptomCheckerModal').classList.remove('active');
        addMessage(currentLanguage === 'en' ? 'Analyzing your symptoms...' :
                currentLanguage === 'zu' ? 'Ihlaziya izimpawu zakho...' :
                currentLanguage === 'xh' ? 'Iphonononga iimpawu zakho...' :
                'Ontleed jou simptome...', 'receive');
        
        try {
            // Prepare symptom data
            const symptomData = {
                main_symptom: symptomResponses[0],
                duration: symptomResponses[1],
                severity: symptomResponses[2],
                additional_symptoms: symptomResponses[3],
                lang: currentLanguage
            };
            
            const response = await fetch('/analyze_symptoms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(symptomData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || "Analysis failed");
            }
            
            addMessage(data.analysis, 'receive');
            
        } catch (error) {
            addMessage(currentLanguage === 'en' ? 'Error analyzing symptoms. Please try again.' :
                    currentLanguage === 'zu' ? 'Iphutha ekuhlaziyeni izimpawu. Sicela uzame futhi.' :
                    currentLanguage === 'xh' ? 'Impazamo ekuphengululeni iimpawu. Nceda uzame kwakhona.' :
                    'Fout tydens ontleding van simptome. Probeer asseblief weer.', 'receive');
            console.error('Symptom analysis error:', error);
        }
    }
    
    if (isSpeechRecognitionSupported) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            userInput.focus();
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            addMessage('Sorry, I couldn\'t understand your voice. Please try typing.', 'receive');
        };
    } else {
        voiceBtn.style.display = 'none';
    }
    
    // Toggle chat box with animation
    chatButton.addEventListener('click', function() {
        chatBox.classList.toggle('active');
        if (chatBox.classList.contains('active')) {
            // Remove notification badge when chat is opened
            document.querySelector('.notification-badge').style.display = 'none';
        }
    });
    
    // Close chat
    closeChat.addEventListener('click', function() {
        chatBox.classList.remove('active');
    });
    
    // Open options modal
    addExtra.addEventListener('click', function() {
        optionsModal.classList.add('active');
    });
    
    // Close options modal
    modalClose.addEventListener('click', function() {
        optionsModal.classList.remove('active');
    });
    
    // Open emergency modal
    emergencyBtn.addEventListener('click', function() {
        optionsModal.classList.remove('active');
        emergencyModal.classList.add('active');
    });
    
    // Close emergency modal
    closeEmergency.addEventListener('click', function() {
        emergencyModal.classList.remove('active');
    });
    
    // Print functionality
    printBtn.addEventListener('click', function() {
        // Create a printable summary of the conversation
        const printContent = generatePrintableSummary();
        const printWindow = window.open('', '_blank');
        printWindow.document.write(printContent);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 500);
    });
    
    document.querySelectorAll('.quick-btn').forEach(button => {
        button.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            userInput.value = prompt;
            sendMessage();
        });
    });
    
    if (isSpeechRecognitionSupported) {
        voiceBtn.addEventListener('click', function() {
            try {
                recognition.start();
                addTypingIndicator('Listening...');
                voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                
                recognition.onspeechend = function() {
                    recognition.stop();
                    voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                    removeTypingIndicator();
                };
            } catch (e) {
                console.error('Speech recognition error:', e);
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                removeTypingIndicator();
            }
        });
    }
    
    // Send message function with enhanced features
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'send');
        userInput.value = '';
        
        // Show typing indicator
        addTypingIndicator(currentLanguage === 'en' ? 'EDI is thinking...' : 
                        currentLanguage === 'zu' ? 'EDI iyacabanga...' :
                        currentLanguage === 'xh' ? 'EDI iyacinga...' :
                        currentLanguage === 'af' ? 'EDI dink...':
                        currentLanguage === 'st' ? 'EDI ea nahana...':
                        currentLanguage === 'tn' ? 'EDI e a akanya...':
                        currentLanguage === 'ts' ? 'EDI yi le ku ehleketeni...':
                        currentLanguage === 've' ? 'EDI ri khou humbula...':
                        currentLanguage === 'ss' ? 'EDI uyacabanga...':
                        currentLanguage === 'nso' ? 'EDI e a nagana...':
                        currentLanguage === 'nr' ? 'EDI iyacabanga...' : '');
        
        try {
            const response = await fetch('/get', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    msg: message,
                    lang: currentLanguage 
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || "Request failed");
            }
            
            // Process the response to format disease information, clinics, etc.
            const formattedResponse = formatAIResponse(data.answer);
            addMessage(formattedResponse, 'receive');
            
            // If chat is closed, show notification
            if (!chatBox.classList.contains('active')) {
                document.querySelector('.notification-badge').style.display = 'flex';
            }
            
        } catch (error) {
            addMessage(`Sorry, I encountered an error. Please try again later.`, 'receive');
            console.error('Chat error:', error);
        } finally {
            removeTypingIndicator();
        }
    }
    
    // Format the AI response to handle structured data
    function formatAIResponse(response) {
        // Check if response contains disease information markers
        if (response.includes('<strong>') && response.includes('</strong>')) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = response;
            
            tempDiv.querySelectorAll('strong').forEach(strong => {
                const text = strong.textContent.toLowerCase();
                if (text.includes('symptom')) {
                    strong.parentElement.classList.add('disease-symptoms');
                } else if (text.includes('treatment')) {
                    strong.parentElement.classList.add('disease-treatment');
                } else if (text.includes('prevention')) {
                    strong.parentElement.classList.add('disease-prevention');
                } else if (text.includes('urgent')) {
                    strong.parentElement.classList.add('disease-urgent');
                }
            });
            
            return tempDiv.innerHTML;
        }
        
        return response;
    }
    
    function addTypingIndicator(text) {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <span style="margin-left: 10px; font-size: 12px; color: #666;">${text}</span>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-box-body-${type} animate__animated animate__fadeIn`;
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <p>${text}</p>
            <span>${time}</span>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function generatePrintableSummary() {
        const messages = document.querySelectorAll('.chat-box-body-send, .chat-box-body-receive');
        let html = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Medical Consultation Summary</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
                    .header { text-align: center; margin-bottom: 20px; }
                    .header img { height: 60px; }
                    .message { margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
                    .send { text-align: right; color: #2C50EF; }
                    .receive { text-align: left; }
                    .time { font-size: 11px; color: #777; }
                    .disease-info { margin-left: 15px; border-left: 3px solid #2C50EF; padding-left: 10px; }
                    .urgent { color: #E74C3C; font-weight: bold; }
                    .footer { margin-top: 30px; font-size: 12px; text-align: center; color: #777; }
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Department_of_Health_%28South_Africa%29_logo.svg/1200px-Department_of_Health_%28South_Africa%29_logo.svg.png" alt="SA Health">
                    <h2>Medical Consultation Summary</h2>
                    <p>Generated on ${new Date().toLocaleString()}</p>
                </div>
        `;
        
        messages.forEach(msg => {
            const type = msg.classList.contains('chat-box-body-send') ? 'send' : 'receive';
            const content = msg.querySelector('p').innerHTML;
            const time = msg.querySelector('span').textContent;
            
            html += `
                <div class="message ${type}">
                    <div class="content">${content}</div>
                    <div class="time">${time}</div>
                </div>
            `;
        });
        
        html += `
                <div class="footer">
                    <p>This summary is for informational purposes only and does not replace professional medical advice.</p>
                    <p>For emergencies, call 10177 (Ambulance) or 112 (Cell phone emergency)</p>
                </div>
            </body>
            </html>
        `;
        
        return html;
    }
    
    sendButton.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    
    setTimeout(() => {
        chatBox.classList.add('active');
    }, 1500);
    
    
    document.getElementById('findClinic').addEventListener('click', function() {
        optionsModal.classList.remove('active');
        addMessage("I can help you find nearby clinics. Please share your location or town name.", 'receive');
        
        
        setTimeout(() => {
            const clinics = [
                {
                    name: "Johannesburg Central Clinic",
                    address: "123 Health St, Johannesburg, 2000",
                    hours: "Mon-Fri: 7:30AM-4PM, Sat: 8AM-12PM",
                    phone: "011 123 4567"
                },
                {
                    name: "Soweto Community Health Center",
                    address: "456 Wellness Ave, Soweto, 1809",
                    hours: "Mon-Fri: 8AM-5PM",
                    phone: "011 987 6543"
                }
            ];
            
            let clinicHTML = "<h4>Nearby Clinics:</h4>";
            clinics.forEach(clinic => {
                clinicHTML += `
                    <div class="clinic-card">
                        <div class="clinic-name">${clinic.name}</div>
                        <div class="clinic-address">${clinic.address}</div>
                        <div class="clinic-hours"><i class="far fa-clock"></i> ${clinic.hours}</div>
                        <div class="clinic-phone"><i class="fas fa-phone"></i> ${clinic.phone}</div>
                    </div>
                `;
            });
            
            clinicHTML += "<p>Remember to bring your ID and medical card if you have one.</p>";
            addMessage(clinicHTML, 'receive');
        }, 1000);
    });

    document.getElementById('languageSelect').addEventListener('change', function() {
        currentLanguage = this.value;
        addMessage(`Language changed to ${this.options[this.selectedIndex].text}`, 'receive');
    });
    
    document.getElementById('callAmbulance').addEventListener('click', function() {
        emergencyModal.classList.remove('active');
        addMessage("URGENT: I've prepared emergency information for you. Please call 10177 immediately for an ambulance.", 'receive');
        
        setTimeout(() => {
            addMessage(`
                <div class="urgent-alert">
                    <h5><i class="fas fa-exclamation-triangle"></i> While waiting for the ambulance:</h5>
                    <ul>
                        <li>Stay calm and keep the patient still</li>
                        <li>If unconscious, place in recovery position</li>
                        <li>If bleeding, apply direct pressure with clean cloth</li>
                        <li>Loosen tight clothing around neck and waist</li>
                        <li>Do not give food or drink</li>
                    </ul>
                </div>
            `, 'receive');
        }, 500);
    });
});