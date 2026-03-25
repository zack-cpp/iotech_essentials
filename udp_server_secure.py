import socket
import hmac
import hashlib
import time
import os

PORT = int(os.getenv("PORT"))
SECRET_KEY = os.getenv("SECRET_KEY").encode('utf-8')

# 2. Time window (in seconds) to accept a message. Prevents replay attacks.
MAX_TIME_DIFF = 10

def verify_and_parse(data):
    """
    Expects data in the format: "timestamp|message|signature"
    Returns the message if valid, or None if invalid/forged/expired.
    """
    try:
        decoded_data = data.decode('utf-8', errors='ignore')
        parts = decoded_data.split('|')
        
        if len(parts) != 3:
            return None # Malformed packet
            
        timestamp_str, msg, signature = parts
        timestamp = int(timestamp_str)
        
        # Check against replay attacks (is the timestamp too old or from the future?)
        current_time = int(time.time())
        if abs(current_time - timestamp) > MAX_TIME_DIFF:
            print("--> Rejected: Message expired (Replay Attack?)")
            return None

        # Re-calculate the HMAC signature to verify authenticity
        payload = f"{timestamp_str}|{msg}".encode('utf-8')
        expected_mac = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
        
        # Securely compare signatures to prevent timing attacks
        if hmac.compare_digest(expected_mac, signature):
            return msg
        else:
            print("--> Rejected: Invalid Signature")
            return None
            
    except Exception as e:
        return None

def sign_message(msg):
    """
    Packages a reply into the format: "timestamp|message|signature"
    """
    timestamp_str = str(int(time.time()))
    payload = f"{timestamp_str}|{msg}".encode('utf-8')
    signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
    return f"{timestamp_str}|{msg}|{signature}".encode('utf-8')

def start_udp_responder():
    print(f"Starting Secured UDP Broadcast Responder on port {PORT}...")

    # Setup UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind to all interfaces
    sock.bind(('', PORT))

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            
            # Pass the raw data through our security check
            valid_msg = verify_and_parse(data)

            if valid_msg == "DISCOVER_SERVER":
                print(f"--> Authenticated discovery request from ESP32 at {addr[0]}")
                
                # Sign the reply so the ESP32 knows it's talking to the real server
                secure_reply = sign_message("I_AM_SERVER")
                sock.sendto(secure_reply, addr)

        except KeyboardInterrupt:
            print("\nShutting down.")
            break

if __name__ == '__main__':
    start_udp_responder()
