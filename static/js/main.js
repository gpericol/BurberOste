document.addEventListener('DOMContentLoaded', () => {
    // Elementi UI
    const recordButton = document.getElementById('recordButton');
    const transcriptionDiv = document.getElementById('transcription');
    const statusDiv = document.getElementById('status');
    
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
        updateStatus('Connesso al server', 'alert-success');
    });
    
    socket.on('disconnect', () => {
        updateStatus('Disconnesso dal server', 'alert-danger');
    });
    
    socket.on('transcription_result', (data) => {
        transcriptionDiv.innerHTML = `<p>${data.text}</p>`;
        updateStatus('Trascrizione completata', 'alert-success');
    });
    
    socket.on('error', (data) => {
        updateStatus(`Errore: ${data.message}`, 'alert-danger');
    });
    
    // Funzione per aggiornare lo stato
    function updateStatus(message, className = 'alert-info') {
        statusDiv.className = `alert ${className}`;
        statusDiv.textContent = message;
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
                updateStatus('Elaborazione audio...', 'alert-info');
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
            
            updateStatus('Pronto per registrare', 'alert-success');
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
            
            transcriptionDiv.innerHTML = '<p class="text-muted">Registrazione in corso...</p>';
        }
    }
    
    // Funzione per interrompere la registrazione
    function stopRecording() {
        if (isRecording) {
            isRecording = false;
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                updateStatus('Registrazione terminata, in elaborazione...', 'alert-info');
            }
        }
    }
    
    // Gestione eventi del pulsante
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
    
    // Gestione della barra spaziatrice
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