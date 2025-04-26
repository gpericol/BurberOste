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
    const streamInterval = 1000; // Intervallo fisso a 1 secondo
    let streamIntervalId;
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
                
                // Avvia lo streaming periodico
                streamIntervalId = setInterval(() => {
                    if (audioChunks.length > 0) {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        sendAudioChunk(audioBlob);
                        // Non svuotiamo completamente i chunk per evitare interruzioni
                        // ma teniamo solo l'ultimo per assicurare la continuità
                        audioChunks = audioChunks.slice(-1);
                    }
                }, streamInterval);
            };
            
            // Quando la registrazione è completa
            mediaRecorder.onstop = () => {
                updateStatus('L\'oste sta ascoltando...', 'alert-info');
                recordButton.classList.remove('active');
                
                // Interrompi lo streaming periodico
                clearInterval(streamIntervalId);
                
                // Invia tutti i chunk rimanenti
                if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    sendAudioChunk(audioBlob);
                    audioChunks = [];
                }
                
                // Notifica il server che la registrazione è terminata
                socket.emit('stop_recording');
            };
            
            updateStatus('Pronto per interagire con l\'oste', 'alert-success');
        } catch (err) {
            console.error('Errore accesso al microfono:', err);
            updateStatus(`Errore accesso al microfono: ${err.message}`, 'alert-danger');
        }
    }
    
    // Funzione per inviare un chunk audio al server
    function sendAudioChunk(blob) {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = () => {
            const base64data = reader.result;
            socket.emit('audio_data', base64data);
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
            
            // Notifica il server dell'inizio della registrazione
            socket.emit('start_recording');
            
            // Avvia la registrazione con timeslice più piccolo
            mediaRecorder.start(10); // Raccoglie chunk ogni 10ms per maggiore precisione
            
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