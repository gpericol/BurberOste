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
        this.sympathyBar = document.getElementById('sympathy-bar');
        this.npcImage = document.querySelector('.npc-avatar img'); // Riferimento all'immagine dell'NPC
        
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
    
    // Aggiorna la visualizzazione del livello di simpatia
    updateSympathyBar(level) {
        if (!this.sympathyBar) return;
        
        // Calcola la percentuale per la larghezza della barra di progresso
        const percentage = (level / 10) * 100;
        
        // Aggiorna la larghezza della barra
        this.sympathyBar.style.width = `${percentage}%`;
        
        // Aggiorna il testo della barra
        this.sympathyBar.textContent = `${level}/10`;
        
        // Aggiorna l'attributo aria-valuenow per l'accessibilità
        this.sympathyBar.setAttribute('aria-valuenow', level);
        
        // Cambia il colore della barra in base al livello di simpatia
        if (level < 3) {
            this.sympathyBar.className = 'progress-bar bg-danger';
        } else if (level < 7) {
            this.sympathyBar.className = 'progress-bar bg-warning';
        } else {
            this.sympathyBar.className = 'progress-bar bg-success';
        }
        
        // Aggiorna l'immagine dell'NPC in base al livello di simpatia
        this.updateNpcImage(level);
    }
    
    // Funzione per aggiornare l'immagine dell'NPC in base al livello di simpatia
    updateNpcImage(level) {
        if (!this.npcImage) return;
        
        let imageName;
        if (level < 4) {
            imageName = 'npc_0.png';
        } else if (level <= 7) {
            imageName = 'npc_1.png';
        } else {
            imageName = 'npc_2.png';
        }
        
        // Aggiorna l'src dell'immagine
        const basePath = this.npcImage.src.substring(0, this.npcImage.src.lastIndexOf('/') + 1);
        this.npcImage.src = basePath + imageName;
    }
    
    // Gestisce una risposta dell'NPC
    handleNpcResponse(data) {
        // Aggiungi il messaggio dell'utente alla conversazione (se presente)
        if (data.user_message) {
            this.addToConversation(data.user_message, 'user');
        }
        
        // Aggiungi la risposta dell'NPC alla conversazione
        this.addToConversation(data.text, 'npc', data.npc_name);
        
        // Aggiorna la barra di simpatia se il dato è presente
        if (data.sympathy_level !== undefined) {
            this.updateSympathyBar(data.sympathy_level);
        }
        
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