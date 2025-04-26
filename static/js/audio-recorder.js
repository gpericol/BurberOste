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
        
        // Timer per limitare la registrazione a 8 secondi
        this.recordingTimer = null;
        this.maxRecordingTime = 8000; // 8 secondi in millisecondi
        
        // Elementi per la barra di progresso
        this.progressContainer = document.getElementById('recording-progress-container');
        this.progressBar = document.getElementById('recording-progress-bar');
        this.progressInterval = null;
        this.startTime = 0;
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
                audioBitsPerSecond: 32000
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
            
            // Inizializza e mostra la barra di progresso
            this.showProgressBar();
        };
        
        // Quando la registrazione è completa
        this.mediaRecorder.onstop = () => {
            this.updateStatus('L\'oste sta ascoltando...', 'alert-info');
            
            // Nasconde la barra di progresso
            this.hideProgressBar();
            
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
            
            // Imposta il timer per fermare automaticamente dopo 8 secondi
            this.recordingTimer = setTimeout(() => {
                if (this.isRecording) {
                    console.log('Limite di 8 secondi raggiunto, arresto automatico della registrazione');
                    this.stopRecording();
                }
            }, this.maxRecordingTime);
            
            this.updateStatus('Sto ascoltando... (max 8 secondi)', 'alert-warning');
            return true;
        }
        
        return false;
    }
    
    // Funzione per interrompere la registrazione
    stopRecording() {
        // Cancella il timer se esistente
        if (this.recordingTimer) {
            clearTimeout(this.recordingTimer);
            this.recordingTimer = null;
        }
        
        // Ferma l'aggiornamento della barra di progresso
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
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
    
    // Funzioni per la gestione della barra di progresso
    showProgressBar() {
        // Mostra il contenitore della barra di progresso
        if (this.progressContainer) {
            this.progressContainer.style.display = 'block';
        }
        
        // Resetta la barra
        if (this.progressBar) {
            this.progressBar.style.width = '0%';
            this.progressBar.setAttribute('aria-valuenow', '0');
        }
        
        // Registra il tempo di inizio
        this.startTime = Date.now();
        
        // Imposta un intervallo per aggiornare la barra ogni 100ms
        this.progressInterval = setInterval(() => {
            this.updateProgressBar();
        }, 100);
    }
    
    updateProgressBar() {
        if (!this.isRecording || !this.progressBar) return;
        
        // Calcola il tempo trascorso in millisecondi
        const elapsedTime = Date.now() - this.startTime;
        
        // Calcola la percentuale completata (0-100)
        const percentage = Math.min((elapsedTime / this.maxRecordingTime) * 100, 100);
        
        // Aggiorna la barra di progresso
        this.progressBar.style.width = percentage + '%';
        this.progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    hideProgressBar() {
        // Ferma l'aggiornamento
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        // Nascondi il contenitore
        if (this.progressContainer) {
            this.progressContainer.style.display = 'none';
        }
    }
}

// Esporta la classe
export default AudioRecorder;