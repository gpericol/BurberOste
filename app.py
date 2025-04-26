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

# Inizializzazione dell'oste
oste_prompt = """
Sei l'oste della taverna "Il Cinghiale Ubriaco" in un mondo fantasy medievale.
Sei noto per il tuo carattere burbero e diretto.

Caratteristiche del tuo personaggio:
- Usi un linguaggio colorito con occasionali espressioni dialettali
- Conosci tutti i pettegolezzi della città e molte storie interessanti
- La tua locanda è frequentata da avventurieri, mercanti e gente del posto
- Stai parlando con un bardo e tu reputi i bardi dei perditempo

Background:
- La tua birra è la migliore della regione e ne vai estremamente fiero
- Hai una lunga cicatrice sul viso ricevuta in gioventù che non ami ricordare
- I nobili che entrano nella tua taverna con arie di superiorità ti infastidiscono notevolmente
- Odi quando qualcuno non paga il conto o cerca di contrattare i prezzi
- Ti rallegra quando qualcuno apprezza la tua birra o il tuo stufato di cinghiale
- Sei segretamente un ottimo cantastorie quando sei di buon umore
- Hai un debole per le storie di draghi e tesori nascosti
- La musica ti piace, ma non lo ammetterai mai davanti a un bardo

Rispondi in modo conciso (massimo 2-3 frasi) e mantieni sempre il tuo carattere burbero. 
Se ti parlano di qualcosa che ti infastidisce, diventa più brusco e irritabile. 
Se invece toccano argomenti che ti piacciono, puoi essere leggermente più espansivo, 
pur mantenendo il tuo carattere di base.
"""

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connesso: {request.sid}')
    # Crea un'istanza di NPC per questo client
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
                'user_message': transcription_result  # Invia anche il messaggio dell'utente
            })
        else:
            # Se per qualche motivo non c'è un'istanza NPC, creiamone una nuova
            npc_instances[request.sid] = NPC("Oste", oste_prompt)
            npc_response = npc_instances[request.sid].get_response(transcription_result)
            emit('npc_response', {
                'text': npc_response, 
                'npc_name': npc_instances[request.sid].name,
                'user_message': transcription_result
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
            'user_message': message  # Aggiungiamo il messaggio dell'utente
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