import json
import os
import random
import warnings

warnings.filterwarnings("ignore")

# Try loading spacy
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except Exception:
    SPACY_AVAILABLE = False

# TF-IDF for intelligent document search
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

# Gemini AI via direct REST API (no SDK needed)
import urllib.request
import urllib.error
import time

GEMINI_AVAILABLE = True

# ============================================================
# Gemini AI Integration (REST API)
# ============================================================
_gemini_api_key = None
_gemini_configured = False
_gemini_error = ""
_gemini_model_name = ""
_gemini_base_url = "https://generativelanguage.googleapis.com/v1beta"

# Models to try in order (newest/fastest first)
_MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

def _gemini_request(prompt_text, retries=3):
    """Make a REST API call to Gemini with auto-retry and model fallback."""
    global _gemini_model_name
    
    if not _gemini_api_key:
        return None
    
    # Build model list: current model first, then fallbacks
    models = [_gemini_model_name] + [m for m in _MODEL_FALLBACKS if m != _gemini_model_name]
    
    for model in models:
        for attempt in range(retries):
            try:
                url = f"{_gemini_base_url}/models/{model}:generateContent?key={_gemini_api_key}"
                payload = json.dumps({
                    "contents": [{"parts": [{"text": prompt_text}]}]
                })
                
                req = urllib.request.Request(
                    url,
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                
                response = urllib.request.urlopen(req, timeout=60)
                result = json.loads(response.read().decode("utf-8"))
                
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "")
                        if text:
                            # Remember which model worked
                            _gemini_model_name = model
                            return text
                return None
                
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limited - wait and retry
                    if attempt < retries - 1:
                        time.sleep((attempt + 1) * 5)
                        continue
                    else:
                        # Try next model
                        break
                elif e.code == 404:
                    # Model not found - try next model
                    break
                else:
                    try:
                        e.read()
                    except Exception:
                        pass
                    if attempt < retries - 1:
                        time.sleep(2)
                        continue
                    break
            except Exception:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                break
    
    return None

def configure_gemini(api_key):
    """Configure Gemini AI with user's API key."""
    global _gemini_api_key, _gemini_configured, _gemini_error, _gemini_model_name
    
    if not api_key:
        _gemini_configured = False
        _gemini_error = "No API key provided"
        return False, _gemini_error
    
    api_key = api_key.strip().strip('"').strip("'")
    if not api_key.startswith("AIza"):
        _gemini_configured = False
        _gemini_error = "Invalid key format"
        return False, _gemini_error
    
    _gemini_api_key = api_key
    _gemini_model_name = "gemini-2.5-flash-lite"
    _gemini_configured = True
    _gemini_error = ""
    return True, "Connected (gemini-2.5-flash-lite)"

def get_gemini_error():
    return _gemini_error

def is_gemini_active():
    return _gemini_configured and _gemini_api_key is not None

def _ask_gemini(user_input, context=""):
    """Send a query to Gemini AI with placement assistant context."""
    if not is_gemini_active():
        return None
    
    system_prompt = (
        "You are CrackPlacement AI, a placement preparation assistant for B.Tech students. "
        "You help with HR interview questions, technical concepts (OOP, DBMS, OS, DSA, Python, Java), "
        "aptitude preparation, resume tips, and placement strategies. "
        "Give detailed, well-structured answers with examples. Use markdown formatting with bold headers and bullet points. "
        "Keep answers focused and practical for interview preparation."
    )
    
    if context:
        prompt = (
            f"{system_prompt}\n\n"
            f"Context from student's documents:\n---\n{context}\n---\n\n"
            f"Answer: {user_input}"
        )
    else:
        prompt = f"{system_prompt}\n\nStudent's question: {user_input}"
    
    result = _gemini_request(prompt)
    if result:
        return result
    return "⏳ AI is busy. Please wait a moment and try again."

def _ask_gemini_raw(prompt):
    """Send a raw prompt to Gemini. Returns text or None."""
    if not is_gemini_active():
        return None
    return _gemini_request(prompt)


# ============================================================
# PDF Document Store - Supports multiple PDFs
# ============================================================
class DocumentStore:
    """AI-powered document store that indexes and searches across multiple PDFs."""
    
    def __init__(self):
        self.documents = {}
        self.chunks = []
        self.chunk_sources = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._is_indexed = False
    
    def add_document(self, filename, text):
        self.documents[filename] = text
        self._is_indexed = False
    
    def remove_document(self, filename):
        if filename in self.documents:
            del self.documents[filename]
            self._is_indexed = False
    
    def clear(self):
        self.documents.clear()
        self.chunks.clear()
        self.chunk_sources.clear()
        self.vectorizer = None
        self.tfidf_matrix = None
        self._is_indexed = False
    
    def _chunk_text(self, text, chunk_size=300, overlap=50):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) > 30:
                chunks.append(chunk)
        return chunks
    
    def build_index(self):
        if not self.documents or not SKLEARN_AVAILABLE:
            return
        
        self.chunks = []
        self.chunk_sources = []
        
        for filename, text in self.documents.items():
            doc_chunks = self._chunk_text(text)
            self.chunks.extend(doc_chunks)
            self.chunk_sources.extend([filename] * len(doc_chunks))
        
        if self.chunks:
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=10000,
                ngram_range=(1, 2)
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
            self._is_indexed = True
    
    def search(self, query, top_k=3):
        if not self._is_indexed:
            self.build_index()
        
        if not self._is_indexed or not self.chunks:
            return None
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05:
                results.append({
                    "text": self.chunks[idx],
                    "source": self.chunk_sources[idx],
                    "score": float(similarities[idx])
                })
        
        return results if results else None
    
    def get_context_for_query(self, query, top_k=3):
        """Get relevant document context as a string for Gemini."""
        results = self.search(query, top_k)
        if not results:
            return ""
        return "\n\n".join([f"[From {r['source']}]: {r['text']}" for r in results])
    
    def get_summary(self):
        if not self.documents:
            return "No documents loaded."
        lines = []
        for fname, text in self.documents.items():
            word_count = len(text.split())
            lines.append(f"📄 **{fname}** — {word_count:,} words")
        return "\n".join(lines)
    
    def get_document_count(self):
        return len(self.documents)
    
    def get_total_words(self):
        return sum(len(t.split()) for t in self.documents.values())


# Global document store
doc_store = DocumentStore()

# ============================================================
# Intent matching from Q&A database
# ============================================================
def load_intents():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'qa_database.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"intents": []}


def _format_doc_results(results):
    response = "📄 **From your uploaded documents:**\n\n"
    seen_sources = set()
    for r in results:
        source = r["source"]
        if source not in seen_sources:
            response += f"📎 *Source: {source}*\n"
            seen_sources.add(source)
        text = r["text"].strip()
        if len(text) > 500:
            text = text[:500] + "..."
        confidence = r["score"]
        if confidence > 0.3:
            badge = "🟢 High relevance"
        elif confidence > 0.15:
            badge = "🟡 Medium relevance"
        else:
            badge = "🔵 Low relevance"
        response += f"\n> {text}\n\n*{badge} (score: {confidence:.2f})*\n\n---\n"
    return response


def get_response(user_input):
    intents = load_intents()
    user_input_lower = user_input.lower()
    
    # ===========================================
    # PATH A: Gemini AI is active (smart mode)
    # ===========================================
    if is_gemini_active():
        # Get document context if PDFs are loaded
        doc_context = ""
        if doc_store.get_document_count() > 0:
            doc_context = doc_store.get_context_for_query(user_input)
        
        # Let Gemini handle everything
        gemini_response = _ask_gemini(user_input, context=doc_context)
        if gemini_response:
            prefix = ""
            if doc_context:
                prefix = "🤖 *Powered by Gemini AI + Your Documents*\n\n"
            else:
                prefix = "🤖 *Powered by Gemini AI*\n\n"
            return prefix + gemini_response
    
    # ===========================================
    # PATH B: Offline mode (TF-IDF + spaCy)
    # ===========================================
    
    # --- Step 1: Search uploaded documents using TF-IDF ---
    if doc_store.get_document_count() > 0:
        results = doc_store.search(user_input)
        if results:
            top_score = results[0]["score"]
            if top_score > 0.1:
                return _format_doc_results(results)
    
    # --- Step 2: Try spaCy similarity matching ---
    best_intent = None
    highest_similarity = 0.0
    
    if SPACY_AVAILABLE:
        user_doc = nlp(user_input_lower)
        for intent in intents.get("intents", []):
            for pattern in intent["patterns"]:
                pattern_doc = nlp(pattern.lower())
                if user_doc.vector_norm and pattern_doc.vector_norm:
                    similarity = user_doc.similarity(pattern_doc)
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_intent = intent
        
        if highest_similarity > 0.65 and best_intent:
            return random.choice(best_intent["responses"])
    
    # --- Step 3: Fallback keyword matching ---
    best_match = None
    best_score = 0
    
    for intent in intents.get("intents", []):
        for pattern in intent["patterns"]:
            pattern_lower = pattern.lower()
            pattern_words = set(pattern_lower.split())
            input_words = set(user_input_lower.split())
            overlap = len(pattern_words & input_words)
            if pattern_lower in user_input_lower or user_input_lower in pattern_lower:
                overlap += 5
            if overlap > best_score:
                best_score = overlap
                best_match = intent
    
    if best_score >= 2 and best_match:
        return random.choice(best_match["responses"])
    
    # --- Step 4: Smart fallback ---
    if any(word in user_input_lower for word in ["interview", "hr", "hire", "company", "job"]):
        return ("Great question about interviews! Here are some key areas I can help with:\n"
                "- **'Tell me about yourself'** — Self introduction strategies\n"
                "- **'Strengths and weaknesses'** — How to frame them\n"
                "- **'Why should we hire you?'** — Selling yourself\n"
                "- **Placement tips** — Overall preparation strategy\n\n"
                "Try asking one of these specific questions!")
    
    if any(word in user_input_lower for word in ["code", "programming", "language", "software", "develop"]):
        return ("I can help with technical topics! Try asking about:\n"
                "- **OOP concepts** | **DBMS** | **Operating Systems** | **DSA**\n"
                "- **Python or Java** interview questions\n\nAsk me about any of these!")
    
    if any(word in user_input_lower for word in ["aptitude", "quant", "logical", "verbal", "reasoning", "math"]):
        return ("I can help you with aptitude preparation!\n"
                "Head to the **Aptitude Practice** section to take a quiz, or ask me specific questions!")

    if doc_store.get_document_count() > 0:
        return ("I searched your uploaded documents but couldn't find a strong match.\n\n"
                f"📊 **Loaded:** {doc_store.get_document_count()} doc(s), {doc_store.get_total_words():,} words.\n\n"
                "Try rephrasing your question or use more specific terms from your documents.")
    
    return ("I'd be happy to help! Here are some topics I'm great at:\n\n"
            "💼 **HR Questions** | 💻 **Technical Topics** | 📋 **Placement Tips**\n"
            "📄 **PDF Analysis** — Upload PDFs in Study Materials!\n"
            "🤖 **Gemini AI** — Add your free API key in the sidebar for unlimited smart answers!\n\n"
            "Try asking any question!")
