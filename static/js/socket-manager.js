/**
 * socket-manager.js
 * Gestisce la connessione WebSocket e l'invio/ricezione dei messaggi
 */

class SocketManager {
    constructor(onNpcResponse, onStatusUpdate) {
        // Salva i callback
        this.onNpcResponse = onNpcResponse;
        this.updateStatus = onStatusUpdate;
        
        // Inizializza la connessione WebSocket
        this.socket = io();
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Gestione eventi di connessione
        this.socket.on('connect', () => {
            this.updateStatus('Connesso alla taverna', 'alert-success');
        });
        
        this.socket.on('disconnect', () => {
            this.updateStatus('Disconnesso dalla taverna', 'alert-danger');
        });
        
        // Gestione delle risposte dell'NPC
        this.socket.on('npc_response', (data) => {
            this.onNpcResponse(data);
        });
        
        this.socket.on('error', (data) => {
            this.updateStatus(`Errore: ${data.message}`, 'alert-danger');
        });
    }
    
    // Invia l'audio completo al server
    sendAudio(blob) {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = () => {
            const base64data = reader.result;
            // Invia l'audio completo e notifica che la registrazione è terminata
            this.socket.emit('complete_audio', base64data);
        };
    }
}

// Esporta la classe
export default SocketManager;