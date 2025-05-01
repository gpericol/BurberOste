/**
 * speech-synthesis.js
 * Gestisce la sintesi vocale e la generazione di frasi per l'NPC
 */

class SpeechManager {
    constructor() {
        this.initVoices();
    }
    
    // Inizializza le voci per la sintesi vocale
    initVoices() {
        if (window.speechSynthesis) {
            // Quando le voci sono caricate
            if (speechSynthesis.onvoiceschanged !== undefined) {
                speechSynthesis.onvoiceschanged = () => {
                    console.log('Voci caricate:', speechSynthesis.getVoices().length);
                };
            }
            
            // Carica le voci inizialmente
            speechSynthesis.getVoices();
        }
    }
    
    // Funzione per generare una frase gibberish con suoni ispirati allo spagnolo
    generateGibberish() {
        // Array di sillabe tipiche spagnole
        const syllables = [
            'ba', 'ca', 'da', 'es', 'fa', 'ga', 'ha', 'ja', 'la', 'ma', 'na', 'ña', 'pa', 'que', 
            'ra', 'sa', 'ta', 'va', 'xa', 'ya', 'za', 'do', 'ro', 'lo', 'po', 'to', 'co', 'mo',
            'el', 'al', 'de', 'te', 'se', 'mi', 'tu', 'si', 'no', 'por', 'con', 'sin'
        ];
        
        // Parole comuni spagnole da inserire occasionalmente per dare un senso "spagnolo"
        const spanishWords = ['pero', 'hola', 'señor', 'bueno', 'gracias', 'amigo', 'claro', 'ahora', 'vale'];
        
        // Generazione frase casuale
        let phrase = '';
        const wordCount = 3 + Math.floor(Math.random() * 5);
        
        for (let i = 0; i < wordCount; i++) {
            // 30% di probabilità di usare una parola spagnola
            if (Math.random() < 0.3) {
                phrase += spanishWords[Math.floor(Math.random() * spanishWords.length)] + ' ';
            } else {
                // Altrimenti creiamo una parola gibberish
                const syllableCount = 1 + Math.floor(Math.random() * 3); // Da 1 a 3 sillabe
                let word = '';
                
                for (let j = 0; j < syllableCount; j++) {
                    word += syllables[Math.floor(Math.random() * syllables.length)];
                }
                
                phrase += word + ' ';
            }
        }
        
        // Aggiungiamo punteggiatura tipica spagnola
        if (Math.random() < 0.3) {
            phrase = '¡' + phrase.trim() + '!';
        } else if (Math.random() < 0.5) {
            phrase = phrase.trim() + '...';
        } else {
            phrase = phrase.trim() + '.';
        }
        
        // Occasionalmente aggiungiamo un'espressione tipica
        if (Math.random() < 0.2) {
            const expressions = ['¡Madre mía!', '¡Dios mío!', '¡Caramba!', '¡Ay ay ay!', '¡Olé!'];
            phrase = expressions[Math.floor(Math.random() * expressions.length)] + ' ' + phrase;
        }
        
        return phrase;
    }
    
    // Funzione per pronunciare il testo con accento spagnolo
    speakWithSpanishAccent(text) {
        if (!window.speechSynthesis) {
            console.error('Speech Synthesis non supportato dal browser');
            return;
        }
        
        // Ferma eventuali sintesi vocali in corso
        speechSynthesis.cancel();
        
        // Crea un nuovo oggetto di sintesi vocale
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Ottieni le voci disponibili
        const voices = speechSynthesis.getVoices();
        
        // Cerca una voce spagnola
        let spanishVoice = voices.find(voice => voice.lang.includes('es'));
        
        // Se non troviamo una voce spagnola, usiamo la voce predefinita
        if (!spanishVoice) {
            console.warn('Nessuna voce spagnola trovata, uso voce predefinita');
        } else {
            utterance.voice = spanishVoice;
        }
        
        // Impostazioni richieste: pitch basso e velocità alta
        utterance.pitch = 0.5;  // Valore basso = tono più basso (range 0-2)
        utterance.rate = 0.8;   // Valore alto = parlato più veloce (range 0.1-10)
        
        // Riproduci la sintesi vocale
        speechSynthesis.speak(utterance);
    }
    
    // Combina la generazione e la riproduzione vocale
    speakGibberish() {
        const gibberish = this.generateGibberish();
        this.speakWithSpanishAccent(gibberish);
        return gibberish;
    }
}

// Esporta la classe
export default SpeechManager;