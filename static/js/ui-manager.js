/**
 * ui-manager.js
 * Gestisce l'interfaccia utente e l'interazione con gli elementi
 */

class UIManager {
    constructor(speechManager) {
        // Elementi UI
        this.recordButton = document.getElementById('recordButton');
        this.transcriptionDiv = document.getElementById('transcription');
        this.statusDiv = document.getElementById('status');
        this.conversationBox = document.getElementById('conversation-box');
        this.npcName = document.getElementById('npc-name');
        
        // Reference al gestore della sintesi vocale
        this.speechManager = speechManager;
    }
    
    // Funzione per aggiornare lo stato
    updateStatus(message, className = 'alert-info') {
        this.statusDiv.className = `alert ${className} small p-2`;
        this.statusDiv.textContent = message;
    }
    
    // Funzione per aggiungere messaggi alla conversazione
    addToConversation(message, type, speaker = '') {
        const messageElement = document.createElement('div');
        messageElement.className = type === 'npc' ? 'npc-message mb-3' : 'user-message mb-3 text-end';
        
        if (type === 'npc') {
            messageElement.innerHTML = `<strong>${speaker}:</strong> <span>${message}</span>`;
            // Aggiunge una classe che potrebbe essere usata per stilizzare
            messageElement.classList.add('npc-response');
            
            // Genera e pronuncia gibberish con accento spagnolo quando l'NPC risponde
            this.speechManager.speakGibberish();
        } else {
            messageElement.innerHTML = `<span>${message}</span>`;
        }
        
        // Aggiungi il messaggio alla conversazione
        this.conversationBox.appendChild(messageElement);
        
        // Scroll al fondo della conversazione
        this.conversationBox.scrollTop = this.conversationBox.scrollHeight;
    }
    
    // Gestisce una risposta dell'NPC
    handleNpcResponse(data) {
        // Aggiungi il messaggio dell'utente alla conversazione (se presente)
        if (data.user_message) {
            this.addToConversation(data.user_message, 'user');
        }
        
        // Aggiungi la risposta dell'NPC alla conversazione
        this.addToConversation(data.text, 'npc', data.npc_name);
        
        this.updateStatus('L\'oste ha risposto', 'alert-success');
    }
    
    // Configura gli event listeners per i pulsanti
    setupButtonListeners(onStartRecording, onStopRecording) {
        // Gestione eventi del pulsante di registrazione
        this.recordButton.addEventListener('mousedown', onStartRecording);
        this.recordButton.addEventListener('touchstart', (e) => {
            e.preventDefault(); // Previeni eventi touch duplicati
            onStartRecording();
        });
        this.recordButton.addEventListener('mouseup', onStopRecording);
        this.recordButton.addEventListener('mouseleave', onStopRecording);
        this.recordButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            onStopRecording();
        });
    }
    
    // Configura gli event listeners per la tastiera
    setupKeyboardListeners(onStartRecording, onStopRecording, isRecordingActive) {
        // Gestione della barra spaziatrice per la registrazione
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !isRecordingActive()) {
                e.preventDefault(); // Previeni lo scroll della pagina
                onStartRecording();
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (e.code === 'Space' && isRecordingActive()) {
                onStopRecording();
            }
        });
    }
    
    // Segnala visivamente che la registrazione è attiva
    setRecordingActive(isActive) {
        if (isActive) {
            this.recordButton.classList.add('active');
        } else {
            this.recordButton.classList.remove('active');
        }
    }
}

// Esporta la classe
export default UIManager;