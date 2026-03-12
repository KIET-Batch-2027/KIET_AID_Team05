import os
import csv
import re
import string
from collections import OrderedDict

class TranslationService:
    """
    Translation service that uses a single clean dataset file (dataset.csv).
    Supports bidirectional translation between English, Bodo, and Mizo.
    
    Dataset format: english,bodo,mizo,category
    """
    
    def __init__(self):
        """Initialize the translation service by loading the dataset once at startup."""
        self.dataset = []
        self.translation_index = {'english': {}, 'bodo': {}, 'mizo': {}}
        self._load_dataset()
    
    def _load_dataset(self):
        """
        Load dataset.csv once at application startup.
        
        Requirements:
        - Load ONLY from dataset.csv
        - Remove duplicates (keep first occurrence)
        - Trim spaces from all fields
        - Convert English text to lowercase for matching
        - Validate all rows have english, bodo, and mizo values
        """
        dataset_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'dataset.csv')
        
        if not os.path.exists(dataset_path):
            print(f"[ERROR] Dataset file not found: {dataset_path}")
            return
        
        try:
            seen_english = set()
            
            with open(dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Extract and trim fields
                    english = row.get('english', '').strip()
                    bodo = row.get('bodo', '').strip()
                    mizo = row.get('mizo', '').strip()
                    category = row.get('category', '').strip()
                    
                    # Skip rows with missing values
                    if not english or not bodo or not mizo:
                        continue
                    
                    # Skip duplicate English entries (keep first occurrence)
                    english_lower = english.lower()
                    if english_lower in seen_english:
                        continue
                    
                    seen_english.add(english_lower)
                    
                    # Store the row
                    entry = {
                        'english': english,
                        'bodo': bodo,
                        'mizo': mizo,
                        'category': category
                    }
                    
                    self.dataset.append(entry)
                    
                    # Build indices for fast lookup
                    # English -> Bodo, Mizo
                    self.translation_index['english'][english_lower] = {
                        'bodo': bodo,
                        'mizo': mizo
                    }
                    
                    # Bodo -> English, Mizo
                    bodo_lower = bodo.lower()
                    self.translation_index['bodo'][bodo_lower] = {
                        'english': english,
                        'mizo': mizo
                    }
                    
                    # Mizo -> English, Bodo
                    mizo_lower = mizo.lower()
                    self.translation_index['mizo'][mizo_lower] = {
                        'english': english,
                        'bodo': bodo
                    }
            
            print(f"[SUCCESS] Loaded {len(self.dataset)} translations from dataset.csv")
            print(f"  - English entries: {len(self.translation_index['english'])}")
            print(f"  - Bodo entries: {len(self.translation_index['bodo'])}")
            print(f"  - Mizo entries: {len(self.translation_index['mizo'])}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load dataset: {e}")
            import traceback
            traceback.print_exc()
    
    def _clean_text(self, text):
        """
        Clean text for matching:
        - Convert to lowercase
        - Strip whitespace
        - Keep punctuation (for now, will strip if needed)
        """
        if not text:
            return ''
        return text.strip().lower()
    
    def _remove_punctuation(self, text):
        """Remove punctuation from text."""
        return text.translate(str.maketrans('', '', string.punctuation))
    
    def _detect_language(self, text):
        """
        Detect the language of input text.
        
        Returns: 'english', 'bodo', 'mizo', or None
        """
        if not text:
            return None
        
        text_clean = self._clean_text(text)
        
        # Check if text matches any entry in the indices
        if text_clean in self.translation_index['english']:
            return 'english'
        elif text_clean in self.translation_index['bodo']:
            return 'bodo'
        elif text_clean in self.translation_index['mizo']:
            return 'mizo'
        
        # Check word-by-word for phrases
        words = text_clean.split()
        if len(words) > 1:
            # Check if most words are in one language
            english_count = sum(1 for word in words if word in self.translation_index['english'])
            bodo_count = sum(1 for word in words if word in self.translation_index['bodo'])
            mizo_count = sum(1 for word in words if word in self.translation_index['mizo'])
            
            max_count = max(english_count, bodo_count, mizo_count)
            if max_count > 0:
                if english_count == max_count:
                    return 'english'
                elif bodo_count == max_count:
                    return 'bodo'
                elif mizo_count == max_count:
                    return 'mizo'
        
        return None
    
    def translate_word(self, word, source_lang, target_lang):
        """
        Translate a single word.
        
        Word search logic:
        - Convert to lowercase
        - Remove punctuation
        - Search in dataset
        
        Returns: Translated word or error message
        """
        if not word:
            return "Translation not found in dataset"
        
        clean_word = self._clean_text(self._remove_punctuation(word))
        
        if not clean_word:
            return "Translation not found in dataset"
        
        source_lang = source_lang.lower()
        target_lang = target_lang.lower()
        
        # Same language, return original
        if source_lang == target_lang:
            return word
        
        # Look up in index
        if source_lang in self.translation_index:
            if clean_word in self.translation_index[source_lang]:
                result = self.translation_index[source_lang][clean_word].get(target_lang, '')
                if result:
                    return result
        
        return "Translation not found in dataset"
    
    def translate(self, text, source_lang=None, target_lang='mizo'):
        """
        Translate text in all directions.
        
        Supports:
        - English -> Bodo
        - English -> Mizo
        - Bodo -> English
        - Bodo -> Mizo
        - Mizo -> English
        - Mizo -> Bodo
        
        Args:
            text: Text to translate
            source_lang: Source language ('english', 'bodo', 'mizo') - auto-detect if None
            target_lang: Target language (default: 'mizo')
        
        Returns: Translated text or error message
        """
        if not text:
            return "Translation not found in dataset"
        
        # Normalize language names
        if source_lang:
            source_lang = source_lang.lower()
        target_lang = target_lang.lower()
        
        # Auto-detect source language if not provided
        if source_lang is None:
            source_lang = self._detect_language(text)
            if source_lang is None:
                return "Translation not found in dataset"
        
        # Same language, return original
        if source_lang == target_lang:
            return text.strip()
        
        # ========== Exact Phrase Match ==========
        text_clean = self._clean_text(text)
        
        if source_lang in self.translation_index:
            if text_clean in self.translation_index[source_lang]:
                result = self.translation_index[source_lang][text_clean].get(target_lang, '')
                if result:
                    try:
                        print(f"[PHRASE MATCH] {source_lang}->{target_lang}: '{text}' = '{result}'")
                    except:
                        pass
                    return result
        
        # ========== Word-by-Word Translation ==========
        words = text.split()
        translated_words = []
        translated_count = 0
        
        for word in words:
            # Remove punctuation for matching, but remember if it had any
            punct_suffix = ''
            clean_word = word
            
            if clean_word and clean_word[-1] in string.punctuation:
                punct_suffix = clean_word[-1]
                clean_word = clean_word[:-1]
            
            clean_word_lower = self._clean_text(self._remove_punctuation(clean_word))
            
            if not clean_word_lower:
                translated_words.append(word)
                continue
            
            # Try to translate
            if source_lang in self.translation_index:
                if clean_word_lower in self.translation_index[source_lang]:
                    translation = self.translation_index[source_lang][clean_word_lower].get(target_lang, '')
                    if translation:
                        translated_words.append(translation + punct_suffix)
                        translated_count += 1
                        continue
            
            # If not found, keep original
            translated_words.append(word)
        
        result = ' '.join(translated_words)
        
        try:
            print(f"[WORD-BY-WORD] {source_lang}->{target_lang}: {translated_count}/{len(words)} words translated")
        except:
            pass
        
        # Return result if we found at least one word translation
        if translated_count > 0:
            return result
        
        # No translations found
        return "Translation not found in dataset"
    
    def batch_translate(self, texts, source_lang=None, target_lang='mizo'):
        """
        Translate multiple texts.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language (auto-detect if None)
            target_lang: Target language (default: 'mizo')
        
        Returns: List of translated texts
        """
        results = []
        for text in texts:
            result = self.translate(text, source_lang, target_lang)
            results.append(result)
        return results
    
    def get_supported_languages(self):
        """Get list of supported languages."""
        return ['english', 'bodo', 'mizo']
    
    def get_all_translations(self, source_lang='english'):
        """Get all translations for a given source language."""
        source_lang = source_lang.lower()
        if source_lang in self.translation_index:
            return self.translation_index[source_lang]
        return {}
