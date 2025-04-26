/**
 * main.js
 * File principale che coordina tutte le componenti dell'applicazione
 */

// Importa i moduli
import SpeechManager from './speech-synthesis.js';
import SocketManager from './socket-manager.js';
import AudioRecorder from './audio-recorder.js';
import UIManager from './ui-manager.js';

document.addEventListener('DOMContentLoaded', () => {
    // Inizializza le componenti in ordine
    const initApp = async () => {
        // Inizializza il gestore della sintesi vocale
        const speechManager = new SpeechManager();
        
        // Inizializza il gestore dell'UI
        const uiManager = new UIManager(speechManager);
        
        // Funzione per la gestione delle risposte dell'NPC
        const handleNpcResponse = (data) => {
            uiManager.handleNpcResponse(data);
        };
        
        // Inizializza il gestore delle connessioni WebSocket
        const socketManager = new SocketManager(
            handleNpcResponse, 
            (message, className) => uiManager.updateStatus(message, className)
        );
        
        // Funzione per inviare l'audio registrato
        const handleAudioComplete = (blob) => {
            socketManager.sendAudio(blob);
        };
        
        // Inizializza il registratore audio
        const audioRecorder = new AudioRecorder(
            (message, className) => {
                uiManager.updateStatus(message, className);
                if (message.includes('Registrazione in corso')) {
                    uiManager.setRecordingActive(true);
                } else if (message.includes('Elaborazione') || message.includes('ascoltando')) {
                    uiManager.setRecordingActive(false);
                }
            },
            handleAudioComplete
        );
        
        // Inizializza la registrazione
        await audioRecorder.initialize();
        
        // Configura gli event listeners per i pulsanti
        uiManager.setupButtonListeners(
            () => audioRecorder.startRecording(),
            () => audioRecorder.stopRecording()
        );
        
        // Configura gli event listeners per la tastiera
        uiManager.setupKeyboardListeners(
            () => audioRecorder.startRecording(),
            () => audioRecorder.stopRecording(),
            () => audioRecorder.isActive()
        );
    };
    
    // Avvia l'applicazione
    initApp().catch(err => {
        console.error('Errore durante l\'inizializzazione:', err);
    });
});