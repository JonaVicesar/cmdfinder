"""
Searching and matching logic
"""
import re
import unicodedata
from difflib import SequenceMatcher

def normalize(text):
    """
    Converts text for comparison without distinguishing between hyphens, underscores, or spaces

    'Delete_branch' is 'delete branch'
    'DELETE-BRANCH' is 'delete branch'
    """
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text) #NFKD is 'Normalization Form Compatibility Decomposition' simply replaces compatibility characters with their preferred representations (removing accents for example)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[-_]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_key(text):
    """
    Converts an action name into a key for use as a dictionary/JSON key 'Delete Branch' to 'delete-branch'

    Different from normalize(): this produces hyphens for JSON normalize() produces spaces for comparison
    """
    text = normalize(text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    return text


def score_text(query, candidate):
    """
    Score from 0 to 100 indicating how closely 'query' matches 'candidate'
    3 levels 
    100 exact matches 
    75-95 one contains the other (delete Delete_branch)
    0-70 similar (del Delete_branch)
    """
    q = normalize(query)
    c = normalize(candidate)
    if not q or not c:
        return 0
    if q == c:
        return 100

    """
    the floor is 75 (any containment is worth more than letter similarity alone), the aggregate ceiling is 20,
    so the maximum for this level that is 95 is always below the 100% for an exact match, length determines how much of those 20 points use

    example:
    query="eliminar" (8 letters) vs candidate="eliminar rama" (13 letters) 
    length = 8/13 aprox 0,615 
    0,615 * 20 aprox 12,3
    score = 87,3
    """
    if q in c or c in q:
        length = len(q) / max(len(c), 1)
        return 75 + min(length * 20, 20)
    return SequenceMatcher(None, q, c).ratio() * 70


def search_program(name, data):
    """Find the program most similar to 'name' within 'data' """
    if name in data:
        #print("no se", name)
        return name, 100
    best, best_score = None, 0
    for p in data:
        s = score_text(name, p)
        if s > best_score:
            best, best_score = p, s
    return best, best_score


def search_actions(query, actions):

    """
    Searches for 'query' among the actions (key + aliases), returns a list of (score, key, info) for those that exceed the minimun
    ordered from highest to lowest score
    """
    minimun = 40
    result = []
    for key, info in actions.items():
        print("find actions", key)
        best_options = [key] + info.get("aliases", [])
        best_score = max(score_text(query, c) for c in best_options)
        if best_score >= minimun:
            result.append((best_score, key, info))
    result.sort(key=lambda x: x[0], reverse=True)
    return result