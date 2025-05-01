import openai
import json

class NPC:
    HISTORY_LIMIT = 10
    
    def __init__(self, name, prompt):
        self.name = name
        self.prompt = prompt
        self.history = []  # Cronologia della conversazione
        self.sympathy = 0  # Livello di simpatia iniziale (scala 0-10)   

    def _add_to_history(self, role, content):
        self.history.append({"role": role, "content": content})
        self.history = self.history[-NPC.HISTORY_LIMIT:]
    
    
    def get_response(self, user_message):
        try:
            self._add_to_history("user", user_message)
            
            messages = [
                {"role": "system", "content": self.prompt}
            ]
            
            messages.extend(self.history)
                        
            try:
                client = openai.OpenAI()
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
                    max_tokens=150,
                    temperature=0.8
                )
                
                arguments_raw = response.choices[0].message.function_call.arguments
                arguments = json.loads(arguments_raw)

                text_response = arguments["response"]
                sympathy_change = arguments["sympathy"]

                # scala da 1 a 10
                self.sympathy = max(0, min(10, self.sympathy + sympathy_change))
        
                self._add_to_history("assistant", text_response)

                return text_response
                  
            except Exception as api_error:
                print(f"Errore API OpenAI: {str(api_error)}")
                message = "*L'oste sembra distratto e non risponde...*"
                self._add_to_history("assistant", message)
                return message
            
        except Exception as e:
            error_message = f"Errore nella generazione della risposta: {str(e)}"
            print(error_message)
            return "Hmm... sembra che l'oste sia distratto. Riprova più tardi."
