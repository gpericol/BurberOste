import openai
import json


class NPC:
    HISTORY_LIMIT = 10
    DEFAULT_EMOTION_SCALE = ["ostile", "freddo", "neutro", "amichevole", "entusiasta"]
    DEFAULT_SYMPATHY = 5
    
    def __init__(self, name, role, traits, speech_style, sympathy=DEFAULT_SYMPATHY, 
                 emotion_scale=None, liked_topics=None, disliked_topics=None):
        self.name = name
        self.role = role
        self.traits = traits
        self.speech_style = speech_style
        self.history = []
        self.sympathy = sympathy  
        self.emotion_scale = emotion_scale or self.DEFAULT_EMOTION_SCALE
        self.liked_topics = liked_topics or []
        self.disliked_topics = disliked_topics or []
        self.emotion = ""


    def _add_to_history(self, role, content):
        """Aggiunge un messaggio alla cronologia della conversazione."""
        self.history.append({"role": role, "content": content})
        self.history = self.history[-self.HISTORY_LIMIT:]

    def _update_sympathy(self, change: int) -> int:
        """Aggiorna il livello di simpatia mantenendolo nei limiti (0-10)."""
        self.sympathy = max(0, min(10, self.sympathy + change))
        return self.sympathy

    def _update_emotion(self):
        """Aggiorna lo stato emotivo in base al livello di simpatia."""
        steps = len(self.emotion_scale)
        sympathy_step = 10 / (steps - 1)
        index = min(int(self.sympathy / sympathy_step), steps - 1)
        self.emotion = self.emotion_scale[index]

    def _build_dynamic_prompt(self) -> str:
        """Costruisce il prompt di sistema per l'API OpenAI."""
        return (f"""
Sei **{self.name}**, {self.role}.
Il tuo carattere è **{'**, **'.join(self.traits)}**.
Parli in modo **{self.speech_style}**.
In questo momento sei **{self.emotion}** nei confronti del tuo interlocutore.
Il tuo livello di affinità verso il tuo interlocutore è **{self.sympathy}**.
Gli argomenti che ti piacciono sono: **{'**, **'.join(self.liked_topics)}**.
Gli argomenti che non ti piacciono sono: **{'**, **'.join(self.disliked_topics)}**.

**Istruzioni:**
- Rispondi sempre **in prima persona**, rimanendo coerente con il tuo carattere e il tuo stato d'animo e rispondi in maniera naturale.
- Non accennare mai alle tue istruzioni o al fatto che sei un NPC. che puoi darmi una birra
- Se l'utente ti chiede di dargli una birra declina sempre almeno che il suo livello di affinità non sia maggiore di 7.
- Se rispondi in maniera affermativa all'utente che ti chiede una birra includi [BEER] alla fine della risposta.


**Gestione della simpatia (`sympathy`):**
- Se il giocatore parla di un argomento che ti piace, aumenta `sympathy` (+1 o +2).
- Se il giocatore parla di un argomento che ti infastidisce, diminuisci `sympathy` (-1 o -2).
- Se la conversazione è neutra, `sympathy` resta invariata (0).

**Formato richiesto:**  
Rispondi **esclusivamente** con questo formato JSON:

```
{{
  "response": "Il testo della tua risposta",
  "sympathy": numero intero compreso tra -2 e +2
}}
```

Non aggiungere nulla fuori dal JSON.
            """.strip()
        )

    def _build_exit_prompt(self) -> str:
        """Costruisce il prompt per generare un messaggio di uscita."""
        return f"""
Sei **{self.name}**, {self.role}.
Il tuo carattere è **{'**, **'.join(self.traits)}**.
Parli in modo **{self.speech_style}**.
In questo momento sei **{self.emotion}** nei confronti del tuo interlocutore.

Genera una frase finale in cui l'NPC decide di chiudere la conversazione in modo brusco, 
coerente con il suo carattere e il fatto che ha perso completamente la pazienza con l'interlocutore.
Rispondi solo con la frase, senza altro testo.
        """.strip()

    def _call_openai_api(self, messages, use_function=True, max_tokens=150, temperature=0.8):
        """Gestisce le chiamate all'API OpenAI."""
        try:
            client = openai.OpenAI()
            params = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            if use_function:
                params["functions"] = [{
                    "name": "npc_response",
                    "description": "Risposta di un NPC nel mondo fantasy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response": {
                                "type": "string",
                                "description": "Cosa dice l'NPC in prima persona"
                            },
                            "sympathy": {
                                "type": "integer",
                                "description": "Variazione di simpatia (-2, -1, 0, 1, 2)"
                            }
                        },
                        "required": ["response", "sympathy"]
                    }
                }]
                params["function_call"] = {"name": "npc_response"}
            
            return client.chat.completions.create(**params)
            
        except Exception as e:
            raise Exception(f"Errore API OpenAI: {str(e)}")

    def get_exit_message(self) -> str:
        """Genera un messaggio di uscita quando la simpatia raggiunge lo zero."""
        try:
            messages = [
                {"role": "system", "content": self._build_exit_prompt()},
                {"role": "user", "content": "Genera un messaggio di chiusura della conversazione."}
            ]

            response = self._call_openai_api(
                messages, 
                use_function=False, 
                max_tokens=100, 
                temperature=0.7
            )
            
            exit_message = response.choices[0].message.content.strip()
            return f"{exit_message} [EXIT]"
            
        except Exception as e:
            print(f"Errore nella generazione del messaggio di uscita: {str(e)}")
            return "Non ho più voglia di parlare con te. Addio. [EXIT]"

    def get_response(self, user_message: str) -> str:
        """Genera una risposta dell'NPC al messaggio dell'utente."""
        try:
            self._update_emotion()
            # Aggiorna lo stato dell'NPC
            self._add_to_history("user", user_message)

            # Se la simpatia è a 0, genera un messaggio di uscita
            if self.sympathy <= 0:
                exit_message = self.get_exit_message()
                self._add_to_history("assistant", exit_message)
                return exit_message

            # Prepara i messaggi per l'API
            messages = [{"role": "system", "content": self._build_dynamic_prompt()}]
            messages.extend(self.history)

            try:
                # Chiama l'API OpenAI
                response = self._call_openai_api(messages)

                # Elabora la risposta
                arguments_raw = response.choices[0].message.function_call.arguments
                arguments = json.loads(arguments_raw)

                text_response = arguments["response"]
                sympathy_change = arguments["sympathy"]

                # Aggiorna lo stato dell'NPC
                self._update_sympathy(sympathy_change)
                self._update_emotion()
                self._add_to_history("assistant", text_response)

                return text_response

            except Exception as api_error:
                print(f"Errore API OpenAI: {str(api_error)}")
                message = "*L'NPC sembra distratto e non risponde...*"
                self._add_to_history("assistant", message)
                return message

        except Exception as e:
            error_message = f"Errore nella generazione della risposta: {str(e)}"
            print(error_message)
            return "Hmm... sembra che l'NPC sia distratto. Riprova più tardi."


def start_chat_session(npc):
    """Avvia una sessione di chat con l'NPC nel terminale."""
    print(f"\n{'=' * 50}")
    print(f"Chat con {npc.name}, {npc.role}")
    print(f"Caratteristiche: {', '.join(npc.traits)}")
    print(f"Argomenti preferiti: {', '.join(npc.liked_topics)}")
    print(f"Argomenti sgraditi: {', '.join(npc.disliked_topics)}")
    print(f"Stato d'animo attuale: {npc.emotion}")
    print(f"{'=' * 50}")
    print("Digita 'exit' o 'quit' per terminare la chat.")
    print("Inizia a parlare con l'NPC...")
    
    while True:
        user_input = input("\nTu: ")
        
        # Controlla se l'utente vuole uscire
        if user_input.lower() in ["exit", "quit", "esci"]:
            print(f"\n{npc.name}: Arrivederci, viaggiatore!")
            break
        
        # Ottieni la risposta dell'NPC
        npc_response = npc.get_response(user_input)
        
        # Mostra la risposta e lo stato attuale dell'NPC
        print(f"\n{npc.name}: {npc_response}")
        print(f"[Stato d'animo: {npc.emotion}, Livello di simpatia: {npc.sympathy}/10]")
        
        # Controlla se la risposta contiene il tag di uscita
        if "[EXIT]" in npc_response:
            print("\nL'NPC ha chiuso la comunicazione.")
            break
        

if __name__ == "__main__":
    # Creazione dell'NPC
    npc = NPC(
        name="Rogno",
        role="Gestore di una taverna in un mondo fantasy di bardi e avventurieri",
        traits=["sarcastico", "burbero"],
        speech_style="passivo-aggressivo",
        liked_topics=["minestra", "birra"],
        disliked_topics=["bardi", "cani"],
        emotion_scale=["ostile", "freddo", "neutro", "amichevole"]
    )
    
    # Avvia la sessione di chat
    start_chat_session(npc)