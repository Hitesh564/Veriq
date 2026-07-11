import asyncio
import os
import json
import urllib.request
import websockets
from dotenv import load_dotenv

# Load env variables from the root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def list_supported_bidi_models():
    print("--- Listing available models for your API key ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            models = data.get("models", [])
            
            print("\nAvailable models supporting real-time voice (bidiGenerateContent):")
            bidi_models = []
            all_models = []
            for m in models:
                name = m.get("name", "")
                all_models.append(name)
                methods = m.get("supportedGenerationMethods", [])
                if "bidiGenerateContent" in methods:
                    bidi_models.append(name)
                    print(f"  - {name} ({m.get('displayName')})")
            
            if not bidi_models:
                print("  No models found supporting 'bidiGenerateContent' for this API key.")
                print("\nAll models available for your key:")
                for name in all_models:
                    print(f"  - {name}")
    except Exception as e:
        print(f"Failed to query model registry: {e}")

async def debug_connection(model_name):
    print(f"\n--- Testing connection with model: {model_name} ---")
    uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={GEMINI_API_KEY}"
    
    try:
        async with asyncio.timeout(10):
            async with websockets.connect(uri) as ws:
                print("SUCCESS: Established raw WebSocket handshake!")
                
                setup_payload = {
                    "setup": {
                        "model": model_name,
                        "generationConfig": {
                            "responseModalities": ["AUDIO"]
                        }
                    }
                }
                await ws.send(json.dumps(setup_payload))
                print("Sent setup payload. Waiting for response...")
                
                response = await ws.recv()
                print(f"RESPONSE RECEIVED: {response}")
                
    except TimeoutError:
        print("FAILED: Connection timed out.")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"FAILED: Connection closed by server. Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        print(f"FAILED: Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in env.")
        exit(1)
        
    print(f"Loaded GEMINI_API_KEY from env: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-5:] if len(GEMINI_API_KEY) > 10 else ''}")
    
    # Run registry check
    list_supported_bidi_models()
    
    # Run connection test
    models_to_test = [
        "models/gemini-live-2.5-flash-native-audio",
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-exp"
    ]
    
    print("\n--- Running WebSocket Connection Tests ---")
    for m in models_to_test:
        asyncio.run(debug_connection(m))
