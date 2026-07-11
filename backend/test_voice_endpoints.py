import sys
import os
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# Adjust path to import backend app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import engine, init_db
from app.models.interview import Interview, Transcript, EvaluationReport

client = TestClient(app)

def test_voice_flow():
    print("Initializing Database...")
    init_db()

    # 1. Start Voice Session
    print("\n--- Testing: POST /api/interview/start ---")
    payload = {
        "role": "AI Engineer",
        "difficulty": "medium",
        "duration_minutes": 10,
        "mode": "quick"
    }
    
    response = client.post("/api/interview/start", json=payload)
    if response.status_code != 200:
        print(f"FAILED: /api/interview/start returned {response.status_code}")
        print(response.json())
        return
        
    session_data = response.json()
    session_id = session_data.get("session_id")
    print(f"SUCCESS: Voice session started! Session ID: {session_id}")

    # 2. Run Voice Turn (with mock audio URL)
    print("\n--- Testing: POST /api/interview/turn ---")
    mock_audio = "https://vapi-recordings.s3.amazonaws.com/mock-candidate-answer.wav"
    turn_payload = {
        "session_id": session_id,
        "candidate_text": "I built a customized ResNet model in PyTorch for retinal age prediction.",
        "audio_url": mock_audio
    }
    
    response = client.post("/api/interview/turn", json=turn_payload)
    if response.status_code != 200:
        print(f"FAILED: /api/interview/turn returned {response.status_code}")
        print(response.json())
        return
        
    turn_data = response.json()
    print(f"SUCCESS: Interviewer responded: \"{turn_data.get('interviewer_response')}\"")

    # 3. Verify database storage for audio_url
    print("\n--- Verifying: Database audio_url storage ---")
    with Session(engine) as session:
        statement = select(Transcript).where(
            Transcript.interview_id == session_id,
            Transcript.sender == "candidate"
        ).order_by(Transcript.timestamp.desc())
        last_transcript = session.exec(statement).first()
        
        if last_transcript:
            print(f"Found transcript text: \"{last_transcript.text}\"")
            print(f"Found transcript audio_url: \"{last_transcript.audio_url}\"")
            if last_transcript.audio_url == mock_audio:
                print("SUCCESS: audio_url matches mock audio URL perfectly!")
            else:
                print("FAILED: audio_url does not match.")
        else:
            print("FAILED: Transcript row not found.")

    # 4. End Interview manually and verify report generation
    print("\n--- Testing: POST /api/interview/end ---")
    end_payload = {
        "session_id": session_id
    }
    response = client.post("/api/interview/end", json=end_payload)
    if response.status_code != 200:
        print(f"FAILED: /api/interview/end returned {response.status_code}")
        print(response.json())
        return
        
    print(f"SUCCESS: End endpoint response: {response.json()}")

    # 5. Fetch report card
    print("\n--- Testing: GET /api/evaluation/{session_id} ---")
    response = client.get(f"/api/evaluation/{session_id}")
    if response.status_code != 200:
        print(f"FAILED: /api/evaluation/{{session_id}} returned {response.status_code}")
        print(response.json())
        return
        
    report = response.json()
    print(f"SUCCESS: Report retrieved! Overall score: {report.get('overall_score')}%")
    print(f"Hiring recommendation: {report.get('hire_recommendation')} (Confidence: {report.get('confidence_level')})")
    print(f"Ownership score: {report.get('ownership_score')}%")
    print(f"Coverage score: {report.get('interview_completion_score')}%")
    learning_plan = report.get('learning_plan')
    learning_plan_keys = list(learning_plan.keys()) if learning_plan else []
    print(f"Learning plan categories: {learning_plan_keys}")
    
    print("\n================================================")
    print("ALL REST VOICE ENDPOINTS TESTED successfully!")
    print("================================================")

def test_voice_websocket():
    print("\n================================================")
    print("Testing Custom Voice WebSocket Endpoint")
    print("================================================")
    init_db()
    
    # 1. Start Session
    payload = {
        "role": "AI Engineer",
        "difficulty": "medium",
        "duration_minutes": 10,
        "mode": "quick"
    }
    response = client.post("/api/interview/start", json=payload)
    if response.status_code != 200:
        print(f"FAILED: Start session returned {response.status_code}")
        return
    session_id = response.json().get("session_id")
    print(f"Session started: {session_id}")
    
    # 2. Connect via WebSocket
    print(f"Connecting to WebSocket: /api/voice/interview/{session_id} ...")
    try:
        with client.websocket_connect(f"/api/voice/interview/{session_id}") as websocket:
            # Wait for status response
            data = websocket.receive_json()
            print(f"Received message from WebSocket: {data}")
            if data.get("type") == "status":
                print("SUCCESS: Connected to Voice WebSocket and status received!")
            else:
                print(f"FAILED: Received unexpected message: {data}")
    except Exception as e:
        print(f"FAILED: WebSocket connection raised exception: {e}")
        print("Please ensure your DEEPGRAM_API_KEY in the .env file is valid and active.")

if __name__ == "__main__":
    test_voice_flow()
    test_voice_websocket()

