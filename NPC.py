import openai
import json

class NPC:
    HISTORY_LIMIT = 10
    DEFAULT_EMOTION_SCALE = ["ostile", "freddo", "neutro", "amichevole", "entusiasta"]
    DEFAULT_AFFINITY = 5
    
    def __init__(self, name, role, traits, speech_style, affinity=DEFAULT_AFFINITY, 
                 emotion_scale=None, liked_topics=None, disliked_topics=None):
        self.name = name
        self.role = role
        self.traits = traits
        self.speech_style = speech_style
        self.affinity = affinity  
        self.emotion_scale = emotion_scale or self.DEFAULT_EMOTION_SCALE
        self.liked_topics = liked_topics or []
        self.disliked_topics = disliked_topics or []
        self.emotion = ""
        self.conversation_history = []

    def _add_to_history(self, role, player_message):
        if len(self.conversation_history) >= self.HISTORY_LIMIT:
            self.conversation_history.pop(0)
        self.conversation_history.append({"role": role, "content": player_message})
        
    def _update_affinity(self, change: int) -> int:
        self.affinity = max(0, min(10, self.affinity + change))
        return self.affinity

    def _update_emotion(self):
        steps = len(self.emotion_scale)
        affinity_step = 10 / (steps - 1)
        index = min(int(self.affinity / affinity_step), steps - 1)
        self.emotion = self.emotion_scale[index]

    def _build_dynamic_prompt(self) -> str:
        exit_instructions = ""
        if self.affinity <= 1:
            exit_instructions = "* IMPORTANTE: Hai perso la pazienza con il tuo interlocutore. Ora devi rispondere una sola volta e poi chiudere la conversazione bruscamente ed aggiungi l'azione [EXIT]\n"

        return (f"""
Sei {self.name}, {self.role}.
Il tuo carattere è {', '.join(self.traits)}.
Parli in modo {self.speech_style}.
In questo momento sei {self.emotion} nei confronti del tuo interlocutore.
Il tuo livello di affinità verso il tuo interlocutore è {self.affinity}.
Gli argomenti che ti piacciono sono: {', '.join(self.liked_topics)}.
Gli argomenti che non ti piacciono sono: {', '.join(self.disliked_topics)}.

# Istruzioni
* Rispondi sempre in prima persona, rimanendo coerente con il tuo carattere e il tuo stato d'animo.
* Se ti viene chiesta una birra offrila solo se l'affinità è alta (>=5), altrimenti non offrirla.
* non dire mai direttamente quello che ti piace o non ti piace, ma lascia intendere il tuo stato d'animo.
* Non usare mai il termine "affinità" o "emozione" nella tua risposta.
{exit_instructions}

# Gestione della affinità (affinity)
* Se il giocatore parla di un argomento che ti piace, aumenta affinity (+1 o +2).
* Se il giocatore parla di un argomento che ti infastidisce, diminuisci affinity (-1 o -2).
* Se la conversazione è neutra, affinity resta invariata (0).

# Gestione dell'azione (action):
* None: Non eseguire alcuna azione.
* [EXIT]: Chiudi la conversazione e non rispondere più.
* [BEER]: Offri una birra al giocatore.

#Formato richiesto:
Rispondi esclusivamente con questo formato JSON:

{{
  "response": "Il testo della tua risposta",
  "affinity": numero intero compreso tra -2 e +2,
  "action": "eventuale azione da eseguire"
}}

Non aggiungere nulla fuori dal JSON.
""".strip())

    def _call_openai_api(self, messages, use_function=True, max_tokens=500, temperature=0.8):
        #print(messages)
        try:
            client = openai.OpenAI()
            params = {
                "model": "gpt-4.1-nano",
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
                            },
                            "action": {
                                "type": "string",
                                "description": "Azione da eseguire (opzionale)"
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
        try:
            self._update_emotion()
            
            # Memorizziamo il messaggio dell'utente
            self._add_to_history("user", user_message)

            messages = [{"role": "system", "content": self._build_dynamic_prompt()}]
            messages.extend(self.conversation_history)

            try:
                response = self._call_openai_api(messages)

                arguments_raw = response.choices[0].message.function_call.arguments
                arguments = json.loads(arguments_raw)

                text_response = arguments["response"]
                affinity_change = arguments["affinity"]
                arguments_action = arguments.get("action", None)
                print("Affinity change:", affinity_change)
                print("Azione:", arguments_action)

                self._update_affinity(affinity_change)
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
            message = "Hmm... sembra che l'NPC sia distratto. Riprova più tardi."
            return message


def start_chat_session(npc):
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
        
        if user_input.lower() in ["exit", "quit", "esci"]:
            print(f"\n{npc.name}: Arrivederci, viaggiatore!")
            break
        
        npc_response = npc.get_response(user_input)
        
        print(f"\n{npc.name}: {npc_response}")
        print(f"[Stato d'animo: {npc.emotion}, Livello di affinità: {npc.affinity}/10]")
        
        if "[EXIT]" in npc_response:
            print("\nL'NPC ha chiuso la comunicazione.")
            break

        if "[BEER]" in npc_response:
            print("\nHai ricevuto una birra!")
            break


if __name__ == "__main__":
    npc = NPC(
        name="Rogno",
        role="Gestore di una taverna in un mondo fantasy di bardi e avventurieri",
        traits=["sarcastico", "burbero"],
        speech_style="passivo-aggressivo",
        liked_topics=["minestra", "birra"],
        disliked_topics=["bardi", "cani"],
        emotion_scale=["ostile", "freddo", "neutro", "amichevole"]
    )
    
    start_chat_session(npc)