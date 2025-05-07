from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import base64
import os
import io
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from npc import NPC  # Corretto il nome del modulo (minuscolo)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiavesegreta12345')  # Prende la SECRET_KEY dal .env o usa un default
socketio = SocketIO(app, cors_allowed_origins="*")

# Dizionario per memorizzare le istanze di NPC per ogni client
npc_instances = {}

# Configurazione dell'NPC Oste
oste_config = {
    "name": "Oste Genzo",
    "role": "Gestore di una taverna in un mondo fantasy",
    "traits": ["sarcastico", "burbero", "esperto di birre"],
    "speech_style": "diretto e colloquiale",
    "liked_topics": ["birra", "affari", "storie di viaggiatori"],
    "disliked_topics": ["elfi", "magia", "debiti"]
}

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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connesso: {request.sid}')
    # Crea un'istanza di NPC per questo client con i parametri corretti
    npc_instances[request.sid] = NPC(
        name=oste_config["name"],
        role=oste_config["role"],
        traits=oste_config["traits"],
        speech_style=oste_config["speech_style"],
        liked_topics=oste_config["liked_topics"],
        disliked_topics=oste_config["disliked_topics"]
    )
    emit('connect_response', {'status': 'connesso'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnesso: {request.sid}')
    # Elimina istanze NPC per questo client
    if request.sid in npc_instances:
        del npc_instances[request.sid]

@socketio.on('complete_audio')
def handle_complete_audio(data):
    print(f'Ricevuto audio completo dal client: {request.sid}')
    
    try:
        # Decodifica i dati base64
        if 'base64,' in data:
            data = data.split('base64,')[1]
        
        audio_data = base64.b64decode(data)
        
        # Crea un buffer in memoria per la trascrizione
        audio_buffer = io.BytesIO(audio_data)
        
        # Trascrivi l'audio
        transcription_result = transcribe_audio_from_buffer(audio_buffer)
        
        # Invia la trascrizione all'NPC e ottieni la risposta
        if request.sid in npc_instances:
            npc_response = npc_instances[request.sid].get_response(transcription_result)
            # Invia la risposta dell'NPC al client
            emit('npc_response', {
                'text': npc_response, 
                'npc_name': npc_instances[request.sid].name,
                'user_message': transcription_result,
                'sympathy_level': npc_instances[request.sid].affinity  # Corretto da sympathy a affinity
            })
        else:
            # Se per qualche motivo non c'è un'istanza NPC, creiamone una nuova
            npc_instances[request.sid] = NPC(
                name=oste_config["name"],
                role=oste_config["role"],
                traits=oste_config["traits"],
                speech_style=oste_config["speech_style"],
                liked_topics=oste_config["liked_topics"],
                disliked_topics=oste_config["disliked_topics"]
            )
            npc_response = npc_instances[request.sid].get_response(transcription_result)
            emit('npc_response', {
                'text': npc_response, 
                'npc_name': npc_instances[request.sid].name,
                'user_message': transcription_result,
                'sympathy_level': npc_instances[request.sid].affinity  # Corretto da sympathy a affinity
            })
        
        print(f"Risposta dell'NPC inviata al client: {request.sid}")
    except Exception as e:
        print(f"Errore durante l'elaborazione dell'audio: {e}")
        emit('error', {'message': f'Errore: {str(e)}'})

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
            response_format="text",
            language="it"
        )
        fine_chiamata = time.time()
        tempo_impiegato = fine_chiamata - inizio_chiamata
        print(f"Tempo impiegato per la trascrizione: {tempo_impiegato:.2f} secondi")
        
        return transcription
    except Exception as e:
        print(f"Errore durante la trascrizione: {e}")
        return f"Errore durante la trascrizione: {str(e)}"

if __name__ == '__main__':
    socketio.run(app, debug=True)