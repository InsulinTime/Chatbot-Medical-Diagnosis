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
    
    // Check if speech recognition is available
    const isSpeechRecognitionSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    let recognition;
    
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
    
    // Quick action buttons
    document.querySelectorAll('.quick-btn').forEach(button => {
        button.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            userInput.value = prompt;
            sendMessage();
        });
    });
    
    // Voice input
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
        addTypingIndicator('EDI is thinking...');
        
        try {
            const response = await fetch('/get', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ msg: message })
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
            
            // Add classes for styling
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
    
    // Add typing indicator
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
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Add message to chat with animation
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
    
    // Generate printable summary of conversation
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
    
    // Send on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send on Enter key
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Initial greeting with delay
    setTimeout(() => {
        chatBox.classList.add('active');
    }, 1500);
    
    // Add clinic finder functionality
    document.getElementById('findClinic').addEventListener('click', function() {
        optionsModal.classList.remove('active');
        addMessage("I can help you find nearby clinics. Please share your location or town name.", 'receive');
        
        // In a real implementation, you would use geolocation API here
        // For now, we'll simulate it
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
    
    // Add emergency call functionality
    document.getElementById('callAmbulance').addEventListener('click', function() {
        emergencyModal.classList.remove('active');
        addMessage("URGENT: I've prepared emergency information for you. Please call 10177 immediately for an ambulance.", 'receive');
        
        // In a real app, this would initiate a phone call
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