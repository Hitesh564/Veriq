import urllib.parse
from app.config import DEEPGRAM_API_KEY, TECHNICAL_VOCAB

def get_deepgram_url() -> str:
    """
    Constructs the Deepgram Live WS URL with technical vocabulary boosting query parameters.
    """
    base_url = "wss://api.deepgram.com/v1/listen"
    params = {
        "model": "nova-2",
        "smart_format": "true",
        "interim_results": "true",
        "endpointing": "300",  # ms of silence after speech to trigger speech-final transcript
    }
    query_string = urllib.parse.urlencode(params)
    
    # Append keywords
    keyword_params = []
    for word in TECHNICAL_VOCAB:
        boosted_word = f"{word}:3"
        keyword_params.append(f"keywords={urllib.parse.quote(boosted_word)}")
        
    if keyword_params:
        query_string += "&" + "&".join(keyword_params)
        
    return f"{base_url}?{query_string}"

def get_deepgram_headers() -> dict:
    """
    Returns headers needed for establishing a WebSocket connection to Deepgram.
    """
    return {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }
