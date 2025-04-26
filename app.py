from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import base64
import os
import io
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiavesegreta12345')  # Prende la SECRET_KEY dal .env o usa un default
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurazione OpenAI
try:
    # Prende la API key dal .env
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        print("\n⚠️ API key di OpenAI non trovata nel file .env!")
        client = None
    else:
        client = OpenAI(api_key=openai_api_key)
        print("API key caricata dal file .env")
except Exception as e:
    print(f"Errore durante l'inizializzazione del client OpenAI: {e}")
    print("L'applicazione verrà avviata, ma la trascrizione audio non funzionerà.")
    client = None

# Dizionario per tenere traccia delle registrazioni attive
active_recordings = {}
# Dizionario per tenere traccia dei timestamp dell'ultimo chunk audio ricevuto
last_audio_timestamp = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connesso: {request.sid}')
    emit('connect_response', {'status': 'connesso'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnesso: {request.sid}')
    # Elimina eventuali registrazioni attive per questo client
    if request.sid in active_recordings:
        del active_recordings[request.sid]
    if request.sid in last_audio_timestamp:
        del last_audio_timestamp[request.sid]

@socketio.on('start_recording')
def handle_start_recording():
    print(f'Inizio registrazione per il client: {request.sid}')
    active_recordings[request.sid] = io.BytesIO()
    last_audio_timestamp[request.sid] = time.time()

@socketio.on('audio_data')
def handle_audio_data(data):
    if request.sid not in active_recordings:
        active_recordings[request.sid] = io.BytesIO()
        
    # Aggiorna il timestamp dell'ultimo chunk ricevuto
    last_audio_timestamp[request.sid] = time.time()
    
    # Decodifica i dati base64
    try:
        # Rimuovi l'intestazione del DataURL se presente
        if 'base64,' in data:
            data = data.split('base64,')[1]
            
        audio_data = base64.b64decode(data)
        buffer = active_recordings[request.sid]
        buffer.write(audio_data)
        
        print(f"Ricevuti {len(audio_data)} bytes di audio dal client: {request.sid}")
    except Exception as e:
        print(f"Errore durante la decodifica dell'audio: {e}")

@socketio.on('stop_recording')
def handle_stop_recording():
    if request.sid not in active_recordings:
        emit('error', {'message': 'Nessuna registrazione attiva trovata per questo client'})
        return
    
    # Aspetta un breve momento per assicurarsi che tutti i pacchetti audio siano arrivati
    # Controlla se è passato del tempo dall'ultimo chunk audio ricevuto
    if request.sid in last_audio_timestamp:
        elapsed = time.time() - last_audio_timestamp[request.sid]
        # Se è passato meno di 0.5 secondi dall'ultimo chunk, attendi un po'
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
    
    try:
        # Ottieni il buffer audio associato al client
        audio_buffer = active_recordings[request.sid]
        
        # Verifica che ci siano dati nel buffer
        audio_buffer.seek(0, io.SEEK_END)
        size = audio_buffer.tell()
        if size == 0:
            emit('error', {'message': 'Nessun dato audio registrato'})
            return
            
        # Reimposta il cursore del buffer all'inizio
        audio_buffer.seek(0)
        
        # Trascrivi l'audio
        transcription_result = transcribe_audio_from_buffer(audio_buffer)
        
        # Invia la trascrizione al client
        emit('transcription_result', {'text': transcription_result})
        
        # Pulizia
        del active_recordings[request.sid]
        if request.sid in last_audio_timestamp:
            del last_audio_timestamp[request.sid]
        
        print(f"Trascrizione completata e inviata al client: {request.sid}")
    except Exception as e:
        print(f"Errore durante la trascrizione: {e}")
        emit('error', {'message': f'Errore durante la trascrizione: {str(e)}'})

def transcribe_audio_from_buffer(audio_buffer):
    if client is None:
        return "Impossibile trascrivere l'audio: il client OpenAI non è inizializzato. Controlla la tua API key."
    
    try:
        audio_buffer.seek(0)
        
        audio_buffer.seek(0, io.SEEK_END)
        buffer_size = audio_buffer.tell()
        audio_buffer.seek(0)
        
        print(f"Dimensione totale dell'audio da trascrivere: {buffer_size} bytes")
        
        temp_file = io.BytesIO(audio_buffer.read())
        temp_file.name = "recording.webm"  # Necessario per OpenAI
        
        # Misura il tempo impiegato dalla chiamata OpenAI
        inizio_chiamata = time.time()
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=temp_file,
            response_format="text"
        )
        fine_chiamata = time.time()
        tempo_impiegato = fine_chiamata - inizio_chiamata
        print(f"Tempo impiegato per la chiamata OpenAI: {tempo_impiegato:.2f} secondi")
        
        return transcription
    except Exception as e:
        print(f"Errore durante la trascrizione: {e}")
        return f"Errore durante la trascrizione: {str(e)}"

if __name__ == '__main__':
    socketio.run(app, debug=True)