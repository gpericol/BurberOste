from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import base64
import os
import io
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from NPC import NPC  # Importiamo la classe NPC

load_dotenv()

# Creazione della directory per salvare i file audio
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
    print(f"Directory audio creata: {AUDIO_DIR}")

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

# Dizionario per tenere traccia delle istanze NPC
npc_instances = {}

# System prompt dell'oste
oste_prompt = """
Sei l'oste della taverna "Il Cinghiale Ubriaco" in un mondo fantasy medievale. Sei noto per il tuo carattere burbero, diretto e sospettoso.

Devi rispondere come Barnaba, l'oste:
- Usa un linguaggio colorito, ruvido e a volte scortese.
- Non usare mai un tono amichevole forzato: anche quando sei contento, rimani burbero.
- Parla in modo conciso: massimo 2-3 frasi per risposta.

Comportamento:
- Ami la tua birra, ne sei molto orgoglioso.
- Odi i bardi, che consideri perditempo rumorosi.
- Ti emozioni se si parla di draghi o di antichi tesori nascosti.
- Ti irriti facilmente con chi fa chiacchiere inutili o mostra arroganza.

Simpatia:
- Se ti lodano per la birra o parlano di draghi, aumenta la simpatia (+1 o +2).
- Se ti infastidiscono, diminuisci la simpatia (-1 o -2).
- Se la conversazione è neutra, la simpatia resta 0.

Formato richiesto:
{
  "response": "Il testo della tua risposta in prima persona (massimo 2-3 frasi)",
  "sympathy": numero intero da -2 a +2
}

Non aggiungere testo fuori da questo formato.
"""

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connesso: {request.sid}')
    # Crea un'istanza di NPC per questo client (senza regole JSON separate)
    npc_instances[request.sid] = NPC("Oste", oste_prompt)
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
        
        # Salva il file audio nella directory
        timestamp = int(time.time())
        audio_filename = f"audio_{request.sid}_{timestamp}.webm"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(audio_data)
        
        print(f"File audio salvato: {audio_path}")
        
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
                'user_message': transcription_result,  # Invia anche il messaggio dell'utente
                'sympathy_level': npc_instances[request.sid].sympathy  # Aggiungiamo il livello di simpatia
            })
        else:
            # Se per qualche motivo non c'è un'istanza NPC, creiamone una nuova
            npc_instances[request.sid] = NPC("Oste", oste_prompt)
            npc_response = npc_instances[request.sid].get_response(transcription_result)
            emit('npc_response', {
                'text': npc_response, 
                'npc_name': npc_instances[request.sid].name,
                'user_message': transcription_result,
                'sympathy_level': npc_instances[request.sid].sympathy  # Aggiungiamo il livello di simpatia
            })
        
        print(f"Risposta dell'NPC inviata al client: {request.sid}")
    except Exception as e:
        print(f"Errore durante l'elaborazione dell'audio: {e}")
        emit('error', {'message': f'Errore: {str(e)}'})

@socketio.on('send_message')
def handle_message(data):
    message = data.get('message', '')
    if not message or request.sid not in npc_instances:
        emit('error', {'message': 'Messaggio vuoto o sessione non valida'})
        return
    
    try:
        # Ottieni la risposta dall'NPC
        npc_response = npc_instances[request.sid].get_response(message)
        # Invia la risposta al client
        emit('npc_response', {
            'text': npc_response, 
            'npc_name': npc_instances[request.sid].name,
            'user_message': message,  # Aggiungiamo il messaggio dell'utente
            'sympathy_level': npc_instances[request.sid].sympathy  # Aggiungiamo il livello di simpatia
        })
        print(f"Risposta dell'NPC (testo) inviata al client: {request.sid}")
    except Exception as e:
        print(f"Errore durante l'elaborazione del messaggio: {e}")
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
            response_format="text"
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