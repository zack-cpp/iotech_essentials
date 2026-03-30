import socket
import struct

# SSDP Multicast Address and Port
MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900
SEARCH_TARGET = 'urn:local-server:service:api:1'

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_ssdp_server():
    local_ip = get_local_ip()
    print(f"Starting SSDP Responder. Mini PC IP: {local_ip}")

    # Setup multicast socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Add SO_REUSEPORT for Linux/Ubuntu resilience
    if hasattr(socket, 'SO_REUSEPORT'):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Bind to all interfaces for the multicast port
    sock.bind(('', MCAST_PORT))

    # Join the multicast group on the specific network interface
    mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(local_ip))
    
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print("Successfully joined multicast group.")
    except OSError as e:
        if e.errno == 98:
            print("Notice: Interface already joined multicast group. Continuing...")
        else:
            raise

    print("Listening for M-SEARCH requests...")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode('utf-8', errors='ignore')

            # Check if it's an M-SEARCH for our specific service
            if "M-SEARCH" in msg and SEARCH_TARGET in msg:
                print(f"--> Discovery request received from ESP32 at {addr[0]}")

                # Construct the standard SSDP HTTP/UDP response
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "CACHE-CONTROL: max-age=1800\r\n"
                    f"ST: {SEARCH_TARGET}\r\n"
                    "USN: uuid:11111111-2222-3333-4444-555555555555::" + SEARCH_TARGET + "\r\n"
                    f"LOCATION: http://{local_ip}:8080/api\r\n"
                    "\r\n"
                )

                # Send the reply directly back to the ESP32
                response_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                response_sock.sendto(response.encode('utf-8'), addr)
                print(f"<-- Sent server IP {local_ip} back to {addr[0]}")
                
        except KeyboardInterrupt:
            print("\nShutting down SSDP server.")
            break
        except Exception as e:
            print(f"Error handling request: {e}")

if __name__ == '__main__':
    start_ssdp_server()
