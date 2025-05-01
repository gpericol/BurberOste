import openai
import json
from typing import List, Dict, Union
from npc_memory import NPCMemory


class NPC:
    """
    Classe per la gestione di un personaggio non giocante (NPC) con memoria e stato emotivo.
    Supporta conversazioni dinamiche con risposte generate tramite OpenAI.
    """
    HISTORY_LIMIT = 10
    DEFAULT_EMOTION_SCALE = ["ostile", "freddo", "neutro", "amichevole", "entusiasta"]
    DEFAULT_AFFINITY = 5
    
    def __init__(self, name, role, traits, speech_style, affinity=DEFAULT_AFFINITY, 
                 emotion_scale=None, liked_topics=None, disliked_topics=None):
        """
        Inizializza un nuovo NPC con caratteristiche e preferenze.
        
        Args:
            name: Nome dell'NPC
            role: Ruolo o occupazione dell'NPC
            traits: Lista di tratti caratteriali
            speech_style: Stile di linguaggio (es. formale, colloquiale)
            affinity: Valore iniziale di affinità (0-10)
            emotion_scale: Scala di emozioni dalla più negativa alla più positiva
            liked_topics: Argomenti che piacciono all'NPC
            disliked_topics: Argomenti che non piacciono all'NPC
        """
        self.name = name
        self.role = role
        self.traits = traits
        self.speech_style = speech_style
        self.history = []
        self.affinity = affinity  
        self.emotion_scale = emotion_scale or self.DEFAULT_EMOTION_SCALE
        self.liked_topics = liked_topics or []
        self.disliked_topics = disliked_topics or []
        self.emotion = ""
        # Inizializza la memoria dell'NPC
        self.memory = NPCMemory()

    def _add_to_history(self, role, content):
        """
        Aggiunge un messaggio alla cronologia della conversazione.
        
        Args:
            role: Ruolo del mittente (user o assistant)
            content: Contenuto del messaggio
        """
        self.history.append({"role": role, "content": content})
        self.history = self.history[-self.HISTORY_LIMIT:]

    def _update_affinity(self, change: int) -> int:
        """
        Aggiorna il livello di affinità mantenendolo nei limiti (0-10).
        
        Args:
            change: Variazione di affinità da applicare
            
        Returns:
            Nuovo valore di affinità
        """
        self.affinity = max(0, min(10, self.affinity + change))
        return self.affinity

    def _update_emotion(self):
        """Aggiorna lo stato emotivo in base al livello di affinità."""
        steps = len(self.emotion_scale)
        affinity_step = 10 / (steps - 1)
        index = min(int(self.affinity / affinity_step), steps - 1)
        self.emotion = self.emotion_scale[index]

    def _build_dynamic_prompt(self) -> str:
        """
        Costruisce il prompt di sistema per l'API OpenAI.
        
        Returns:
            Stringa contenente il prompt di sistema
        """
        # Controlla se l'affinità è bassa e aggiunge istruzioni per l'uscita
        exit_instructions = ""
        if self.affinity <= 1:
            exit_instructions = """
**IMPORTANTE:** L'NPC ha perso la pazienza con l'interlocutore.
Genera una risposta finale in cui l'NPC chiude la conversazione in modo brusco e coerente con il suo carattere.
Alla fine della risposta aggiungi il tag [EXIT].
"""

        return (f"""
Sei **{self.name}**, {self.role}.
Il tuo carattere è **{'**, **'.join(self.traits)}**.
Parli in modo **{self.speech_style}**.
In questo momento sei **{self.emotion}** nei confronti del tuo interlocutore.
Il tuo livello di affinità verso il tuo interlocutore è **{self.affinity}**.
Gli argomenti che ti piacciono sono: **{'**, **'.join(self.liked_topics)}**.
Gli argomenti che non ti piacciono sono: **{'**, **'.join(self.disliked_topics)}**.

**Istruzioni:**
- Rispondi sempre **in prima persona**, rimanendo coerente con il tuo carattere e il tuo stato d'animo e rispondi in maniera naturale.
{exit_instructions}

**Gestione della affinità (`affinity`):**
- Se il giocatore parla di un argomento che ti piace, aumenta `affinity` (+1 o +2).
- Se il giocatore parla di un argomento che ti infastidisce, diminuisci `affinity` (-1 o -2).
- Se la conversazione è neutra, `affinity` resta invariata (0).

**Formato richiesto:**  
Rispondi **esclusivamente** con questo formato JSON:

```
{{
  "response": "Il testo della tua risposta",
  "affinity": numero intero compreso tra -2 e +2
}}
```

Non aggiungere nulla fuori dal JSON.
            """.strip()
        )

    def _call_openai_api(self, messages, use_function=True, max_tokens=150, temperature=0.8):
        """
        Gestisce le chiamate all'API OpenAI.
        
        Args:
            messages: Lista di messaggi per la conversazione
            use_function: Se usare le function calls di OpenAI
            max_tokens: Numero massimo di token nella risposta
            temperature: Temperatura per la generazione (0-1)
            
        Returns:
            Risposta dall'API OpenAI
            
        Raises:
            Exception: In caso di errore nella chiamata API
        """
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
                            "affinity": {
                                "type": "integer",
                                "description": "Variazione di affinità (-2, -1, 0, 1, 2)"
                            }
                        },
                        "required": ["response", "affinity"]
                    }
                }]
                params["function_call"] = {"name": "npc_response"}
            
            return client.chat.completions.create(**params)
            
        except Exception as e:
            raise Exception(f"Errore API OpenAI: {str(e)}")

    def get_response(self, user_message: str) -> str:
        """
        Genera una risposta dell'NPC al messaggio dell'utente.
        
        Args:
            user_message: Messaggio dell'utente/giocatore
            
        Returns:
            Risposta testuale dell'NPC
        """
        try:
            self._update_emotion()
            # Aggiorna lo stato dell'NPC
            self._add_to_history("user", user_message)

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
                affinity_change = arguments["affinity"]

                # Aggiorna lo stato dell'NPC
                self._update_affinity(affinity_change)
                self._update_emotion()
                self._add_to_history("assistant", text_response)
                
                # Aggiungi l'interazione alla memoria
                self.memory.add_interaction(user_message, text_response)

                return text_response

            except Exception as api_error:
                print(f"Errore API OpenAI: {str(api_error)}")
                message = "*L'NPC sembra distratto e non risponde...*"
                self._add_to_history("assistant", message)
                # Aggiungi l'interazione alla memoria anche in caso di errore
                self.memory.add_interaction(user_message, message)
                return message

        except Exception as e:
            error_message = f"Errore nella generazione della risposta: {str(e)}"
            print(error_message)
            message = "Hmm... sembra che l'NPC sia distratto. Riprova più tardi."
            # Aggiungi l'interazione alla memoria anche in caso di errore
            self.memory.add_interaction(user_message, message)
            return message


def start_chat_session(npc):
    """
    Avvia una sessione di chat con l'NPC nel terminale.
    
    Args:
        npc: Istanza della classe NPC con cui chattare
    """
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
        print(f"[Stato d'animo: {npc.emotion}, Livello di affinità: {npc.affinity}/10]")
        
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
 