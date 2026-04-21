#!/usr/bin/env python3
"""
Test script for Phase 2 Chat with History
Verifies session management and conversation continuity
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_response(response_data):
    """Pretty print chat response"""
    print("\n" + "="*60)
    print("ASSISTANT:")
    print(response_data.get("response", ""))
    print("\nSUGGESTIONS:")
    for suggestion in response_data.get("suggestions", []):
        print(f"  - {suggestion}")
    if response_data.get("function_calls"):
        print(f"\nFUNCTION CALLS: {', '.join(response_data['function_calls'])}")
    print("="*60 + "\n")

def test_conversation_history():
    """Test multi-turn conversation with history"""
    print("\n🧪 TEST 1: Conversation History\n")

    # Message 1: Ask about expensive systems
    print("USER: What are the most expensive systems?")
    response1 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "What are the most expensive systems?"
    })
    data1 = response1.json()
    session_id = data1.get("session_id")
    print(f"Session ID: {session_id}")
    print_response(data1)

    time.sleep(1)

    # Message 2: Follow-up using context (should remember "expensive systems")
    print("USER: Which buildings have the top one?")
    response2 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "Which buildings have the top one?",
        "session_id": session_id
    })
    data2 = response2.json()
    print_response(data2)

    time.sleep(1)

    # Message 3: Another follow-up
    print("USER: Show me the trends for that system")
    response3 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "Show me the trends for that system",
        "session_id": session_id
    })
    data3 = response3.json()
    print_response(data3)

    return session_id

def test_session_retrieval(session_id):
    """Test retrieving session history"""
    print("\n🧪 TEST 2: Session Retrieval\n")

    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    session_data = response.json()

    print(f"Session: {session_data['session_id']}")
    print(f"Title: {session_data['title']}")
    print(f"Messages: {session_data['message_count']}")
    print(f"Created: {session_data['created_at']}")
    print(f"Updated: {session_data['updated_at']}")
    print("\nConversation History:")
    for i, msg in enumerate(session_data['messages'], 1):
        role = msg['role'].upper()
        content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"{i}. [{role}] {content}")

def test_multiple_sessions():
    """Test creating and managing multiple sessions"""
    print("\n🧪 TEST 3: Multiple Sessions\n")

    # Create session 1
    print("Creating Session 1: About costs")
    response1 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "What are the costs?"
    })
    session1_id = response1.json()["session_id"]
    print(f"Session 1 ID: {session1_id}")

    # Create session 2
    print("Creating Session 2: About risks")
    response2 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "What are the highest risks?"
    })
    session2_id = response2.json()["session_id"]
    print(f"Session 2 ID: {session2_id}")

    # List all sessions
    print("\nListing all sessions:")
    sessions_response = requests.get(f"{BASE_URL}/api/sessions")
    sessions = sessions_response.json()["sessions"]
    for session in sessions:
        print(f"  - {session['session_id'][:8]}... | {session['title'][:40]} | {session['message_count']} msgs")

    return session1_id, session2_id

def test_session_isolation(session1_id, session2_id):
    """Test that sessions are isolated from each other"""
    print("\n🧪 TEST 4: Session Isolation\n")

    # Continue session 1 - should remember costs context
    print("Session 1 - Follow up about costs:")
    response1 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "Show me more details",
        "session_id": session1_id
    })
    print("Response mentions costs:", "cost" in response1.json()["response"].lower())

    # Continue session 2 - should remember risks context
    print("Session 2 - Follow up about risks:")
    response2 = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "Show me more details",
        "session_id": session2_id
    })
    print("Response mentions risks:", "risk" in response2.json()["response"].lower())

def test_session_deletion(session_id):
    """Test deleting a session"""
    print("\n🧪 TEST 5: Session Deletion\n")

    # Delete session
    print(f"Deleting session: {session_id}")
    delete_response = requests.delete(f"{BASE_URL}/api/sessions/{session_id}")
    print(f"Status: {delete_response.json()['status']}")

    # Try to retrieve deleted session (should fail)
    print("Attempting to retrieve deleted session...")
    get_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    if get_response.status_code == 404:
        print("✓ Session not found (expected)")
    else:
        print("✗ Session still exists (unexpected)")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 2 CHAT HISTORY TESTS")
    print("="*60)

    try:
        # Test conversation history
        session_id = test_conversation_history()

        # Test session retrieval
        test_session_retrieval(session_id)

        # Test multiple sessions
        session1_id, session2_id = test_multiple_sessions()

        # Test session isolation
        test_session_isolation(session1_id, session2_id)

        # Test session deletion
        test_session_deletion(session1_id)

        print("\n✅ ALL TESTS COMPLETED\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("Make sure the server is running: python backend/main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
