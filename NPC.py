import openai
import os
import json

class NPC:
    def __init__(self, name, prompt):
        """
        Inizializza un NPC con un nome, un prompt di sistema e un livello di simpatia.
        
        Args:
            name (str): Il nome dell'NPC
            prompt (str): Il prompt di sistema che definisce le caratteristiche dell'NPC
        """
        self.name = name
        self.prompt = prompt
        self.history = []  # Cronologia della conversazione
        self.sympathy = 0  # Livello di simpatia iniziale (scala 0-10)

    def add_to_history(self, role, content):
        """
        Aggiungi un messaggio alla cronologia della conversazione.
        
        Args:
            role (str): Il ruolo del messaggio ('user' o 'assistant')
            content (str): Il contenuto del messaggio
        """
        self.history.append({"role": role, "content": content})
        
        # Mantieni la cronologia a una lunghezza ragionevole (ultime 10 interazioni = 20 messaggi)
        if len(self.history) > 20:
            # Rimuovi i messaggi più vecchi, mantenendo il contesto recente
            self.history = self.history[-20:]
    
    def update_sympathy(self, change):
        """
        Aggiorna il livello di simpatia dell'NPC.
        
        Args:
            change (int): Il valore di cambiamento della simpatia (può essere positivo o negativo)
            
        Returns:
            int: Il nuovo livello di simpatia
        """
        self.sympathy += change
        
        # Mantieni il valore entro i limiti 0-10
        if self.sympathy > 10:
            self.sympathy = 10
        elif self.sympathy < 0:
            self.sympathy = 0
            
        return self.sympathy
    
    def get_response(self, user_message):
        """
        Genera una risposta dell'NPC in base al messaggio dell'utente e aggiorna il livello di simpatia.
        
        Args:
            user_message (str): Il messaggio dell'utente
            
        Returns:
            str: La risposta dell'NPC
        """
        try:
            # Aggiungi il messaggio dell'utente alla cronologia
            self.add_to_history("user", user_message)
            
            # Prepara i messaggi per la chiamata API
            messages = [
                {"role": "system", "content": self.prompt}
            ]
            
            # Aggiungi la cronologia della conversazione (già contiene i ruoli user e assistant)
            messages.extend(self.history)
            
            print("messages:", messages)
            
            try:
                # Chiamata a OpenAI API
                client = openai.OpenAI()  # Usa le credenziali dell'ambiente
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    functions=[
                        {
                            "name": "npc_response",
                            "description": "Risposta di un NPC in taverna",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "response": {
                                        "type": "string",
                                        "description": "Cosa dice l'oste in prima persona"
                                    },
                                    "sympathy": {
                                        "type": "integer",
                                        "description": "Variazione di simpatia (-2, -1, 0, 1, 2)"
                                    }
                                },
                                "required": ["response", "sympathy"]
                            }
                        }
                    ],
                    function_call={"name": "npc_response"},
                    temperature=0.8
                )
                
                arguments_raw = response.choices[0].message.function_call.arguments
                arguments = json.loads(arguments_raw)

                text_response = arguments["response"]
                sympathy_change = arguments["sympathy"]

                # Aggiorna il livello di simpatia
                self.update_sympathy(sympathy_change)
                
                # Registra la risposta nella cronologia con il ruolo "assistant"
                self.add_to_history("assistant", text_response)

                return text_response
                  
            except Exception as api_error:
                print(f"Errore API OpenAI: {str(api_error)}")
                message = "*L'oste sembra distratto e non risponde...*"
                self.add_to_history("assistant", message)
                return message
            
        except Exception as e:
            error_message = f"Errore nella generazione della risposta: {str(e)}"
            print(error_message)
            return "Hmm... sembra che l'oste sia distratto. Riprova più tardi."
