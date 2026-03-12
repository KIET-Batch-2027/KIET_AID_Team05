import json
import os
import csv
import re
import string

class TranslationService:
    def __init__(self):
        self.translation_db = self._load_translation_database()
        self.csv_rows = self._load_csv_rows()  # Keep original CSV rows for bidirectional lookup
    
    def _normalize_text(self, text, lang='english'):
        """Normalize text for searching"""
        if not text:
            return ''
        text = text.strip()
        # For all languages, use lowercase for case-insensitive comparison
        text = text.lower()
        return text
    
    def _detect_language(self, text):
        """
        Detect the language of the input text.
        Checks for exact phrase matches first, then checks individual words.
        
        Returns: 'english', 'bodo', 'mizo', or None if unable to detect
        """
        if not text:
            return None
        
        text_normalized = text.strip()
        text_lower = text_normalized.lower()
        
        # Split into words for word-by-word checking
        words = text_lower.split()
        
        # Check in CSV rows for exact matches or word matches
        for row in self.csv_rows:
            # Check English column
            english_val = row.get('English', '').strip().lower()
            if english_val:
                if english_val == text_lower or any(word in english_val.split() for word in words):
                    return 'english'
            
            # Check Bodo column (case-insensitive)
            bodo_val = row.get('Bodo', '').strip().lower()
            if bodo_val and bodo_val != '?':
                if bodo_val == text_lower or any(word == bodo_val.split()[0] if bodo_val.split() else False for word in words):
                    return 'bodo'
            
            # Check Mizo column (case-insensitive)
            mizo_val = row.get('Mizo', '').strip().lower()
            if mizo_val and mizo_val != '?':
                if mizo_val == text_lower or any(word == mizo_val.split()[0] if mizo_val.split() else False for word in words):
                    return 'mizo'
        
        return None
    
    def _load_csv_rows(self):
        """Load CSV rows for bidirectional lookup"""
        rows = []
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'classroom_dataset_complete.csv')
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Skip rows where all language columns are empty
                        english = row.get('English', '').strip()
                        bodo = row.get('Bodo', '').strip()
                        mizo = row.get('Mizo', '').strip()
                        
                        if english or (bodo and bodo != '?') or (mizo and mizo != '?'):
                            rows.append(row)
                
                print(f"[CSV LOADER] Loaded {len(rows)} CSV rows for bidirectional lookup")
                return rows
            except Exception as e:
                print(f"[CSV LOADER] Error loading CSV rows: {e}")
                return []
        return []
    
    def _load_translation_database(self):
        """Load translation database from CSV file with improved error handling"""
        db = {'english': {}, 'bodo': {}, 'mizo': {}}
        
        # Try to load from the comprehensive dataset
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'classroom_dataset_complete.csv')
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    skipped = 0
                    
                    for row in reader:
                        try:
                            # Handle both column names (ID,English,Bodo,Mizo,Category format)
                            english = row.get('English', '').strip()
                            bodo = row.get('Bodo', '').strip()
                            mizo = row.get('Mizo', '').strip()
                            
                            # Skip empty entries
                            if not english and not bodo and not mizo:
                                skipped += 1
                                continue
                            
                            # Add to English index (lowercase for case-insensitive search)
                            if english:
                                english_lower = self._normalize_text(english, 'english')
                                if english_lower not in db['english']:
                                    db['english'][english_lower] = {'bodo': bodo, 'mizo': mizo}
                            
                            # Add to Bodo index (lowercase for case-insensitive search)
                            if bodo and bodo != '?':  # Skip placeholder values
                                bodo_lower = self._normalize_text(bodo, 'bodo')
                                if bodo_lower not in db['bodo']:
                                    db['bodo'][bodo_lower] = {'english': english, 'mizo': mizo}
                            
                            # Add to Mizo index (lowercase for case-insensitive search)
                            if mizo and mizo != '?':  # Skip placeholder values
                                mizo_lower = self._normalize_text(mizo, 'mizo')
                                if mizo_lower not in db['mizo']:
                                    db['mizo'][mizo_lower] = {'english': english, 'bodo': bodo}
                            
                            count += 1
                        except Exception as row_error:
                            skipped += 1
                            continue
                
                print(f"[SUCCESS] Loaded {count} translations from CSV")
                print(f"  - English entries: {len(db['english'])}")
                print(f"  - Bodo entries: {len(db['bodo'])}")
                print(f"  - Mizo entries: {len(db['mizo'])}")
                print(f"  - Skipped: {skipped}")
                
                return db
            except Exception as e:
                print(f"[WARNING] Error loading CSV: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback to hardcoded translations
        print("[WARNING] Using fallback translation database")
        return {
            'english': {
                # Phrases
                'good morning class': {'bodo': 'सुबुं बिहान', 'mizo': 'Zing tlâm ṭha class'},
                'please open your books': {'bodo': 'अननानै नायनि किताबखौ खेव', 'mizo': 'I lehkhabu hung hawng rawh'},
                'do you understand?': {'bodo': 'नों गोजौ खायला?', 'mizo': 'I hrethiam em?'},
                'today we will learn mathematics': {'bodo': 'दिनै बे सान्न्रि होननाय गोनां', 'mizo': 'Tunah Mathematics kan zir dawn'},
                'very good, well done': {'bodo': 'बेयै गोजौ', 'mizo': 'A tha hle'},
                'please be quiet': {'bodo': 'अननानै थिरगोन दङ', 'mizo': 'Dâwiin dâi la'},
                'raise your hand': {'bodo': 'नायनि खुन्थाखौ थोन', 'mizo': 'I kut kalh rawh'},
                'listen carefully': {'bodo': 'मोनो खालाम', 'mizo': 'Ngaithla ṭha rawh'},
                'write this down': {'bodo': 'बेखौ लिरगोन', 'mizo': 'Hei hi ziak rawh'},
                'homework for tomorrow': {'bodo': 'गाबै नुजाथाव जागायनाय गिबि', 'mizo': 'Tukleha tan homework'},
                'excellent work': {'bodo': 'गोजौ लाफा', 'mizo': 'Ṭha tak tak'},
                'sit down please': {'bodo': 'अननानै फुं', 'mizo': 'Thu rawh le'},
                'pay attention': {'bodo': 'मोनो खालाम', 'mizo': 'Ngaithla ṭha rawh'},
                'turn to page': {'bodo': 'फेजखौ हुं', 'mizo': 'Phek kaltlang rawh'},
                'let us begin': {'bodo': 'जिउनां जागाय', 'mizo': 'Kan tan dawn e'},
                'what are you doing': {'bodo': 'नों तुइ तिङ गोबा', 'mizo': 'I ti tawng law em'},
                'hi hello what are you doing': {'bodo': 'सुबुं, नों तुइ तिङ गोबा', 'mizo': 'Chibai, i ti tawng law em'},
                # Single words
                'mathematics': {'bodo': 'सान्न्रि', 'mizo': 'Mathematics'},
                'science': {'bodo': 'बिजान', 'mizo': 'Science'},
                'history': {'bodo': 'बुरुं', 'mizo': 'History'},
                'geography': {'bodo': 'फिथा बिजान', 'mizo': 'Geography'},
                'english': {'bodo': 'आंग्रेजी', 'mizo': 'English'},
                'hello': {'bodo': 'सुबुं', 'mizo': 'Chibai'},
                'hi': {'bodo': 'सुबुं', 'mizo': 'Chibai'},
                'thank you': {'bodo': 'मोजां', 'mizo': 'Ka lawm e'},
                'thanks': {'bodo': 'मोजां', 'mizo': 'Ka lawm e'},
                'yes': {'bodo': 'अं', 'mizo': 'Awle'},
                'no': {'bodo': 'नङा', 'mizo': 'Aih'},
                'you': {'bodo': 'नों', 'mizo': 'I'},
                'are': {'bodo': 'खायला', 'mizo': 'law'},
                'doing': {'bodo': 'गोबा', 'mizo': 'tawng'},
                'what': {'bodo': 'कोन', 'mizo': 'ti'},
                'please help me': {'bodo': 'अननानै आङा मद्द खालाम', 'mizo': 'Min pui ve rawh'},
                'i dont understand': {'bodo': 'आं गोजाखै', 'mizo': 'Ka hrethiam lo'},
                'repeat please': {'bodo': 'अननानै बार हुनाय', 'mizo': 'Nawn lehah sawi leh rawh'},
                'speak slowly': {'bodo': 'थायनै राव', 'mizo': 'Zawi deuh in sawi rawh'},
                'test tomorrow': {'bodo': 'गाबै परिखा', 'mizo': 'Tukleha test'},
                'study hard': {'bodo': 'गोजौनै होनना', 'mizo': 'Chak takin zir rawh'}
            },
            'bodo': {
                'सुबुं बिहान': {'english': 'Good morning', 'mizo': 'Zing tlâm ṭha'},
                'अननानै नायनि किताबखौ खेव': {'english': 'Please open your books', 'mizo': 'I lehkhabu hung hawng rawh'},
                'नों गोजौ खायला?': {'english': 'Do you understand?', 'mizo': 'I hrethiam em?'},
                'बेयै गोजौ': {'english': 'Very good', 'mizo': 'A tha hle'},
                'सुबुं': {'english': 'Hello', 'mizo': 'Chibai'},
                'मोजां': {'english': 'Thank you', 'mizo': 'Ka lawm e'},
                'अं': {'english': 'Yes', 'mizo': 'Awle'},
                'नङा': {'english': 'No', 'mizo': 'Aih'},
                'सान्न्रि': {'english': 'Mathematics', 'mizo': 'Mathematics'},
                'बिजान': {'english': 'Science', 'mizo': 'Science'},
                'नायनि फोरमाखौ खेव': {'english': 'Open your notebooks', 'mizo': 'I lehkhabu hawng rawh'},
                'नायनि किताबखौ बन्द थ': {'english': 'Close your books', 'mizo': 'I lehkhabu khar rawh'},
                'अननानै फुं': {'english': 'Sit down please', 'mizo': 'Thu rawh le'},
                'गासै दिंना': {'english': 'Stand up everyone', 'mizo': 'Mi zawng ding rawh'},
                'नों': {'english': 'You', 'mizo': 'I'},
                'तुइ': {'english': 'Are', 'mizo': 'law'},
                'गोबा': {'english': 'Doing', 'mizo': 'tawng'},
                'सुबुं मा नं थां दङ': {'english': 'Good morning, how are you?', 'mizo': 'Zing tlâm ṭha, i ni ṭha em?'}
            },
            'mizo': {
                'zing tlâm ṭha': {'english': 'Good morning', 'bodo': 'सुबुं बिहान'},
                'i lehkhabu hung hawng rawh': {'english': 'Please open your books', 'bodo': 'अननानै नायनि किताबखौ खेव'},
                'i hrethiam em?': {'english': 'Do you understand?', 'bodo': 'नों गोजौ खायला?'},
                'a tha hle': {'english': 'Very good', 'bodo': 'बेयै गोजौ'},
                'chibai': {'english': 'Hello', 'bodo': 'सुबुं'},
                'ka lawm e': {'english': 'Thank you', 'bodo': 'मोजां'},
                'awle': {'english': 'Yes', 'bodo': 'अं'},
                'aih': {'english': 'No', 'bodo': 'नङा'},
                'mathematics': {'english': 'Mathematics', 'bodo': 'सान्न्रि'},
                'science': {'english': 'Science', 'bodo': 'बिजान'},
                'i lehkhabu hawng rawh': {'english': 'Open your notebooks', 'bodo': 'नायनि फोरमाखौ खेव'},
                'i lehkhabu khar rawh': {'english': 'Close your books', 'bodo': 'नायनि किताबखौ बन्द थ'},
                'thu rawh le': {'english': 'Sit down please', 'bodo': 'अननानै फुं'},
                'mi zawng ding rawh': {'english': 'Stand up everyone', 'bodo': 'गासै दिंना'}
            }
        }
    
    def _translate_word(self, word, source_lang, target_lang):
        """
        Translate a single word.
        
        Returns: Translated word or empty string if not found
        """
        clean_word = word.strip().lower().strip(string.punctuation)
        if not clean_word:
            return ''
        
        # Try CSV first
        for row in self.csv_rows:
            if source_lang == 'english':
                source_col = 'English'
            elif source_lang == 'bodo':
                source_col = 'Bodo'
            elif source_lang == 'mizo':
                source_col = 'Mizo'
            else:
                continue
            
            source_value = row.get(source_col, '').strip()
            if source_value and self._normalize_text(source_value) == clean_word:
                # Found in CSV
                if source_lang == 'english':
                    word_translation = row.get('Bodo' if target_lang == 'bodo' else 'Mizo', '').strip()
                elif source_lang == 'bodo':
                    word_translation = row.get('English' if target_lang == 'english' else 'Mizo', '').strip()
                elif source_lang == 'mizo':
                    word_translation = row.get('English' if target_lang == 'english' else 'Bodo', '').strip()
                else:
                    word_translation = ''
                
                if word_translation and word_translation != '?':
                    return word_translation
        
        # If not found in CSV, try database
        if source_lang in self.translation_db:
            if clean_word in self.translation_db[source_lang]:
                translation_entry = self.translation_db[source_lang][clean_word]
                if target_lang in translation_entry:
                    word_translation = translation_entry[target_lang]
                    if word_translation and word_translation.strip():
                        return word_translation
        
        return ''
    
    def translate(self, text, source_lang=None, target_lang="mizo"):
        """
        Translate text from source language to target language.
        
        If source_lang is None, automatically detect the source language.
        
        Requirements:
        1. Bidirectional translation lookup
        2. Auto-detect source language if not provided
        3. Case-insensitive search
        4. Trim whitespace before matching
        5. Return empty string if not found
        6. Word-by-word translation for sentences
        
        Returns: Translation string or empty string if not found
        """
        if not text:
            return ''
        
        text_normalized = self._normalize_text(text)
        target_lang = target_lang.lower()
        
        # Auto-detect source language if not provided
        if source_lang is None:
            source_lang = self._detect_language(text)
            if source_lang is None:
                # If detection fails, default to English
                source_lang = 'english'
                try:
                    print(f"[AUTO-DETECT] Could not detect language for '{text}', defaulting to English")
                except:
                    pass
        else:
            source_lang = source_lang.lower()
        
        # If source and target are the same, return original text
        if source_lang == target_lang:
            return text.strip()
        
        # ========== STEP 1: Search CSV for exact match ==========
        for row in self.csv_rows:
            match_key = None
            match_data = None
            
            # Determine which column to search based on source language
            if source_lang == 'english':
                source_col = 'English'
                bodo_col = 'Bodo'
                mizo_col = 'Mizo'
            elif source_lang == 'bodo':
                source_col = 'Bodo'
                bodo_col = 'Bodo'
                mizo_col = 'Mizo'
                english_col = 'English'
            elif source_lang == 'mizo':
                source_col = 'Mizo'
                bodo_col = 'Bodo'
                mizo_col = 'Mizo'
                english_col = 'English'
            else:
                continue
            
            # Get the value from the source column and normalize
            source_value = row.get(source_col, '').strip()
            if not source_value or source_value == '?':
                continue
            
            # Compare normalized values (case-insensitive)
            if self._normalize_text(source_value) == text_normalized:
                # Found a match! Now return the target language translation
                if source_lang == 'english':
                    if target_lang == 'bodo':
                        target_value = row.get('Bodo', '').strip()
                    elif target_lang == 'mizo':
                        target_value = row.get('Mizo', '').strip()
                    else:
                        continue
                elif source_lang == 'bodo':
                    if target_lang == 'english':
                        target_value = row.get('English', '').strip()
                    elif target_lang == 'mizo':
                        target_value = row.get('Mizo', '').strip()
                    else:
                        continue
                elif source_lang == 'mizo':
                    if target_lang == 'english':
                        target_value = row.get('English', '').strip()
                    elif target_lang == 'bodo':
                        target_value = row.get('Bodo', '').strip()
                    else:
                        continue
                else:
                    continue
                
                # Skip if target is empty or placeholder
                if target_value and target_value != '?':
                    try:
                        print(f"[CSV MATCH] {source_lang}->{target_lang}: '{text}' = '{target_value}'")
                    except:
                        pass
                    return target_value
        
        # ========== STEP 2: Try database lookup (fallback) ==========
        if source_lang in self.translation_db:
            if text_normalized in self.translation_db[source_lang]:
                translation_entry = self.translation_db[source_lang][text_normalized]
                if target_lang in translation_entry:
                    result = translation_entry[target_lang]
                    if result and result.strip() and result != '?':
                        try:
                            print(f"[DB MATCH] {source_lang}->{target_lang}: '{text}' = '{result}'")
                        except:
                            pass
                        return result
        
        # ========== STEP 3: Word-by-word translation (for phrases) ==========
        # Split text into words and translate each one
        words = text.split()  # Keep original case/punctuation
        
        if len(words) > 1 or (len(words) == 1 and text_normalized not in self.translation_db.get(source_lang, {})):
            # Try word-by-word translation
            translated_words = []
            found_translations = 0
            total_words = 0
            
            for word in words:
                # Remove punctuation for matching but keep track of it
                clean_word = word.strip().lower().strip(string.punctuation)
                if not clean_word:
                    continue
                
                total_words += 1
                word_translation = self._translate_word(clean_word, source_lang, target_lang)
                
                if word_translation:
                    translated_words.append(word_translation)
                    found_translations += 1
                else:
                    # Keep original word if not found
                    translated_words.append(word)
            
            # Return word-by-word translation (even if some words not found)
            if translated_words:
                result = ' '.join(translated_words)
                try:
                    print(f"[WORD-BY-WORD] {source_lang}->{target_lang}: {found_translations}/{total_words} words translated")
                except:
                    pass
                return result
        
        # ========== STEP 4: Not found ==========
        try:
            print(f"[NOT FOUND] {source_lang}->{target_lang}: '{text}' not found in dataset")
        except:
            pass
        return ''
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return ['english', 'bodo', 'mizo']
    
    def add_translation(self, text, source_lang, target_lang, translation):
        """Add new translation to database"""
        text_lower = text.lower().strip()
        source_lang = source_lang.lower()
        target_lang = target_lang.lower()
        
        if source_lang not in self.translation_db:
            self.translation_db[source_lang] = {}
        
        if text_lower not in self.translation_db[source_lang]:
            self.translation_db[source_lang][text_lower] = {}
        
        self.translation_db[source_lang][text_lower][target_lang] = translation
        return True
