from typing import List, Dict

class NPCMemory:
    def __init__(self, max_interactions: int = 40, summary_block_size: int = 20):
        """
        Inizializza il sistema di memoria dell'NPC.
        
        Args:
            max_interactions: Numero massimo di interazioni recenti da mantenere
            summary_block_size: Ogni quante interazioni generare un riassunto
        """
        self.max_interactions = max_interactions
        self.summary_block_size = summary_block_size
        self.interactions: List[Dict[str, str]] = []
        self.summaries: List[str] = []
        self.interaction_count: int = 0
    
    def add_interaction(self, player_msg: str, npc_msg: str) -> None:
        """
        Aggiunge una nuova interazione alla memoria e gestisce i riassunti.
        
        Args:
            player_msg: Messaggio del giocatore
            npc_msg: Risposta dell'NPC
        """
        self.interactions.append({"player": player_msg, "npc": npc_msg})
        self.interaction_count += 1
        
        # Mantiene solo le interazioni recenti entro il limite
        if len(self.interactions) > self.max_interactions:
            self.interactions = self.interactions[-self.max_interactions:]
        
        # Genera un riassunto ogni summary_block_size interazioni
        if self.interaction_count % self.summary_block_size == 0:
            self.summarize_oldest_block()
    
    def summarize_oldest_block(self) -> None:
        """
        Riassume il blocco più vecchio di interazioni non ancora riassunte.
        """
        # Identifica i messaggi da riassumere (i primi summary_block_size)
        messages_to_summarize = self.interactions[:self.summary_block_size]
        
        # Crea un riassunto (placeholder - da implementare con OpenAI)
        summary = self._generate_summary(messages_to_summarize)
        
        # Aggiunge il riassunto alla lista
        self.summaries.append(summary)
        
        # Rimuove i messaggi riassunti se ci sono abbastanza interazioni
        if len(self.interactions) > self.summary_block_size:
            self.interactions = self.interactions[self.summary_block_size:]
    
    def _generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Genera un riassunto delle interazioni.
        
        Args:
            messages: Lista di messaggi da riassumere
            
        Returns:
            Riassunto testuale delle interazioni
        """
        # Implementazione di base (placeholder)
        # In una versione più avanzata, qui si chiamerebbe l'API di OpenAI
        conversation = ""
        for i, msg in enumerate(messages):
            conversation += f"Giocatore: {msg['player']}\n"
            conversation += f"NPC: {msg['npc']}\n"
        
        return f"Riassunto delle interazioni #{len(self.summaries)+1}: {len(messages)} scambi in cui si è parlato di vari argomenti."
    
    def get_recent_interactions(self) -> List[Dict[str, str]]:
        """
        Restituisce tutte le interazioni recenti.
        
        Returns:
            Lista delle interazioni recenti
        """
        return self.interactions
    
    def get_recent_summaries(self, n: int = -1) -> List[str]:
        """
        Restituisce gli ultimi n riassunti.
        
        Args:
            n: Numero di riassunti da restituire (-1 per tutti)
            
        Returns:
            Lista degli ultimi n riassunti
        """
        if n < 0:
            return self.summaries
        return self.summaries[-n:]
    
    def get_memory_snapshot(self) -> Dict:
        """
        Restituisce uno snapshot completo della memoria.
        
        Returns:
            Dizionario con interazioni recenti e riassunti
        """
        return {
            "interactions": self.interactions,
            "summaries": self.summaries,
            "total_interactions": self.interaction_count
        }