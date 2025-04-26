import openai
import os

class NPC:
    def __init__(self, name, prompt):
        """
        Inizializza un NPC con un nome e un prompt di sistema.
        
        Args:
            name (str): Il nome dell'NPC
            prompt (str): Il prompt di sistema che definisce le caratteristiche dell'NPC
        """
        self.name = name
        self.prompt = prompt
        self.history = []  # Cronologia della conversazione
    
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
    
    def get_response(self, user_message):
        """
        Genera una risposta dell'NPC in base al messaggio dell'utente.
        
        Args:
            user_message (str): Il messaggio dell'utente
            
        Returns:
            str: La risposta dell'NPC
        """
        try:
            # Aggiungi il messaggio dell'utente alla cronologia
            self.add_to_history("user", user_message)
            
            # Prepara i messaggi per la chiamata API includendo:
            # 1. Il prompt di sistema
            # 2. La cronologia della conversazione
            messages = [
                {"role": "system", "content": self.prompt}
            ]
            
            # Aggiungi la cronologia della conversazione
            messages.extend(self.history)
            
            try:
                # Chiamata a OpenAI API
                client = openai.OpenAI()  # Usa le credenziali dell'ambiente
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150  # Limite di token per risposte concise
                )
                
                # Estrai la risposta
                message = response.choices[0].message.content
                
            except Exception as api_error:
                print(f"Errore API OpenAI: {str(api_error)}")
                message = "*L'oste sembra distratto e non risponde...*"
            
            # Aggiungi la risposta dell'NPC alla cronologia
            self.add_to_history("assistant", message)
            
            return message
            
        except Exception as e:
            error_message = f"Errore nella generazione della risposta: {str(e)}"
            print(error_message)
            return "Hmm... sembra che l'oste sia distratto. Riprova più tardi."
