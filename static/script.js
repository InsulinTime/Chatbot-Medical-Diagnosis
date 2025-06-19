document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatBox = document.getElementById('chatBox');
    const closeChat = document.getElementById('closeChat');
    const optionsModal = document.getElementById('optionsModal');
    const addExtra = document.getElementById('addExtra');
    const modalClose = document.querySelector('.modal-close-button');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    
    // Toggle chat box
    chatButton.addEventListener('click', function() {
        chatBox.classList.toggle('active');
    });
    
    // Close chat
    closeChat.addEventListener('click', function() {
        chatBox.classList.remove('active');
    });
    
    // Open modal
    addExtra.addEventListener('click', function() {
        optionsModal.classList.add('active');
    });
    
    // Close modal
    modalClose.addEventListener('click', function() {
        optionsModal.classList.remove('active');
    });
    
    // Replace the sendMessage function with this:
    // Replace your sendMessage function with this:
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'send');
        userInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-box-body-receive';
        typingIndicator.innerHTML = `<p><i>EDI is typing...</i></p>`;
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
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
            
            addMessage(data.answer, 'receive');
            
        } catch (error) {
            addMessage(`Error: ${error.message}`, 'receive');
            console.error('Chat error:', error);
        } finally {
            chatMessages.removeChild(typingIndicator);
        }
    }
    
    // Send on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send on Enter key
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Add message to chat
    function addMessage(text, type) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-box-body-${type}`;
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <p>${text}</p>
            <span>${time}</span>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Initial greeting
    setTimeout(() => {
        chatBox.classList.add('active');
    }, 1000);
});