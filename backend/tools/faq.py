import os
import re
from typing import Dict, Any, Set, Optional

KB_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "faq_kb")


def faq_lookup(query: str) -> Dict[str, Any]:
    """Scans the FAQ knowledge base files for matching content or keywords.

    Calculates keyword intersection score across Markdown documents in KB_DIR and
    returns the content of the best matching document.

    Args:
        query: User query string relating to stadium policies.

    Returns:
        A dictionary containing the topic name, full matching content, and
        the relevance score, or an error message if no matches occur.
    """
    if not query:
        return {"error": "Query cannot be empty."}
        
    query_words: Set[str] = set(re.findall(r'\w+', query.lower()))
    if not query_words:
        return {"error": "No searchable keywords found in query."}

    best_match_file: Optional[str] = None
    best_match_content: str = ""
    best_score: int = 0

    if not os.path.exists(KB_DIR):
        return {"error": "FAQ knowledge base directory not found."}

    for filename in os.listdir(KB_DIR):
        if filename.endswith(".md"):
            filepath: str = os.path.join(KB_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content: str = f.read()
                
            # Score based on how many query words are found in the content
            content_lower: str = content.lower()
            score: int = sum(1 for word in query_words if word in content_lower)
            
            if score > best_score:
                best_score = score
                best_match_file = filename
                best_match_content = content

    if best_score > 0 and best_match_file:
        # Return summary/snippet or full text of the best matching document
        return {
            "topic": best_match_file.replace(".md", "").replace("_", " ").title(),
            "content": best_match_content,
            "relevance_score": best_score,
        }
        
    return {
        "error": (
            "No matching FAQ found. For ticketing or special issues, please "
            "visit a Ticket Resolution Desk near Gate A or Gate C."
        )
    }
