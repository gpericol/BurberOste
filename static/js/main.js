document.addEventListener('DOMContentLoaded', () => {
    // Elementi UI
    const recordButton = document.getElementById('recordButton');
    const transcriptionDiv = document.getElementById('transcription');
    const statusDiv = document.getElementById('status');
    const conversationBox = document.getElementById('conversation-box');
    const npcName = document.getElementById('npc-name');
    
    // Variabili per la registrazione
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let audioStream;
    
    // Connessione WebSocket
    const socket = io();
    
    socket.on('connect', () => {
        updateStatus('Connesso alla taverna', 'alert-success');
    });
    
    socket.on('disconnect', () => {
        updateStatus('Disconnesso dalla taverna', 'alert-danger');
    });
    
    // Gestione delle risposte dell'NPC
    socket.on('npc_response', (data) => {
        // Aggiungi il messaggio dell'utente alla conversazione (se presente)
        if (data.user_message) {
            addToConversation(data.user_message, 'user');
        }
        
        // Aggiungi la risposta dell'NPC alla conversazione
        addToConversation(data.text, 'npc', data.npc_name);
        
        updateStatus('L\'oste ha risposto', 'alert-success');
    });
    
    socket.on('error', (data) => {
        updateStatus(`Errore: ${data.message}`, 'alert-danger');
    });
    
    // Funzione per aggiornare lo stato
    function updateStatus(message, className = 'alert-info') {
        statusDiv.className = `alert ${className} small p-2`;
        statusDiv.textContent = message;
    }
    
    // Funzione per aggiungere messaggi alla conversazione
    function addToConversation(message, type, speaker = '') {
        const messageElement = document.createElement('div');
        messageElement.className = type === 'npc' ? 'npc-message mb-3' : 'user-message mb-3 text-end';
        
        if (type === 'npc') {
            messageElement.innerHTML = `<strong>${speaker}:</strong> <span>${message}</span>`;
            // Aggiunge una classe che potrebbe essere usata per stilizzare
            messageElement.classList.add('npc-response');
        } else {
            messageElement.innerHTML = `<span>${message}</span>`;
        }
        
        // Aggiungi il messaggio alla conversazione
        conversationBox.appendChild(messageElement);
        
        // Scroll al fondo della conversazione
        conversationBox.scrollTop = conversationBox.scrollHeight;
    }
    
    // Inizializza la registrazione audio
    async function initRecording() {
        try {
            audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            mediaRecorder = new MediaRecorder(audioStream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            });
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };
            
            // Quando lo stream è pronto
            mediaRecorder.onstart = () => {
                audioChunks = [];
                updateStatus('Registrazione in corso...', 'alert-warning');
                recordButton.classList.add('active');
            };
            
            // Quando la registrazione è completa
            mediaRecorder.onstop = () => {
                updateStatus('L\'oste sta ascoltando...', 'alert-info');
                recordButton.classList.remove('active');
                
                // Crea un blob con tutti i chunk e invialo al server
                if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    sendCompleteAudio(audioBlob);
                    audioChunks = [];
                }
            };
            
            updateStatus('Pronto per interagire con l\'oste', 'alert-success');
        } catch (err) {
            console.error('Errore accesso al microfono:', err);
            updateStatus(`Errore accesso al microfono: ${err.message}`, 'alert-danger');
        }
    }
    
    // Funzione per inviare l'audio completo al server
    function sendCompleteAudio(blob) {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = () => {
            const base64data = reader.result;
            // Invia l'audio completo e notifica che la registrazione è terminata
            socket.emit('complete_audio', base64data);
        };
    }
    
    // Funzione per avviare la registrazione
    function startRecording() {
        if (!mediaRecorder) {
            updateStatus('Microfono non inizializzato', 'alert-danger');
            return;
        }
        
        if (!isRecording) {
            isRecording = true;
            
            // Avvia la registrazione
            mediaRecorder.start();
            
            updateStatus('Sto ascoltando...', 'alert-warning');
        }
    }
    
    // Funzione per interrompere la registrazione
    function stopRecording() {
        if (isRecording) {
            isRecording = false;
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                updateStatus('Elaborazione del messaggio vocale...', 'alert-info');
            }
        }
    }
    
    // Gestione eventi del pulsante di registrazione
    recordButton.addEventListener('mousedown', startRecording);
    recordButton.addEventListener('touchstart', (e) => {
        e.preventDefault(); // Previeni eventi touch duplicati
        startRecording();
    });
    recordButton.addEventListener('mouseup', stopRecording);
    recordButton.addEventListener('mouseleave', stopRecording);
    recordButton.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopRecording();
    });
    
    // Gestione della barra spaziatrice per la registrazione
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && !isRecording) {
            e.preventDefault(); // Previeni lo scroll della pagina
            startRecording();
        }
    });
    
    document.addEventListener('keyup', (e) => {
        if (e.code === 'Space' && isRecording) {
            stopRecording();
        }
    });
    
    // Inizializza la registrazione all'avvio
    initRecording();
});