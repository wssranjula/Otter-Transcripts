"""Test SSL connectivity to Neo4j Aura"""
import ssl
import socket
import certifi

hostname = "220210fe.databases.neo4j.io"
port = 7687

print(f"Testing SSL connection to {hostname}:{port}")
print(f"Using certificates from: {certifi.where()}")

# Create SSL context with certifi certificates
context = ssl.create_default_context(cafile=certifi.where())

try:
    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(f"\n[OK] SSL connection successful!")
            print(f"Protocol: {ssock.version()}")
            print(f"Cipher: {ssock.cipher()}")
            cert = ssock.getpeercert()
            print(f"Certificate subject: {dict(x[0] for x in cert['subject'])}")
except Exception as e:
    print(f"\n[ERROR] SSL connection failed: {e}")
    print("\nThis suggests a certificate verification issue.")
    print("The Neo4j Python driver may need additional SSL configuration.")
