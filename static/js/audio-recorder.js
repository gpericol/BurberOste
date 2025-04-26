/**
 * audio-recorder.js
 * Gestisce la registrazione audio dal microfono
 */

class AudioRecorder {
    constructor(onStatusUpdate, onAudioComplete) {
        // Callback
        this.updateStatus = onStatusUpdate;
        this.onAudioComplete = onAudioComplete;
        
        // Variabili per la registrazione
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.audioStream = null;
    }
    
    // Inizializza la registrazione audio
    async initialize() {
        try {
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            });
            
            this.setupMediaRecorderEvents();
            
            this.updateStatus('Pronto per interagire con l\'oste', 'alert-success');
            return true;
        } catch (err) {
            console.error('Errore accesso al microfono:', err);
            this.updateStatus(`Errore accesso al microfono: ${err.message}`, 'alert-danger');
            return false;
        }
    }
    
    setupMediaRecorderEvents() {
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };
        
        // Quando lo stream è pronto
        this.mediaRecorder.onstart = () => {
            this.audioChunks = [];
            this.updateStatus('Registrazione in corso...', 'alert-warning');
        };
        
        // Quando la registrazione è completa
        this.mediaRecorder.onstop = () => {
            this.updateStatus('L\'oste sta ascoltando...', 'alert-info');
            
            // Crea un blob con tutti i chunk e invialo al server
            if (this.audioChunks.length > 0) {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.onAudioComplete(audioBlob);
                this.audioChunks = [];
            }
        };
    }
    
    // Funzione per avviare la registrazione
    startRecording() {
        if (!this.mediaRecorder) {
            this.updateStatus('Microfono non inizializzato', 'alert-danger');
            return false;
        }
        
        if (!this.isRecording) {
            this.isRecording = true;
            
            // Avvia la registrazione
            this.mediaRecorder.start();
            
            this.updateStatus('Sto ascoltando...', 'alert-warning');
            return true;
        }
        
        return false;
    }
    
    // Funzione per interrompere la registrazione
    stopRecording() {
        if (this.isRecording) {
            this.isRecording = false;
            
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
                this.updateStatus('Elaborazione del messaggio vocale...', 'alert-info');
                return true;
            }
        }
        
        return false;
    }
    
    // Verifica se la registrazione è attiva
    isActive() {
        return this.isRecording;
    }
}

// Esporta la classe
export default AudioRecorder;