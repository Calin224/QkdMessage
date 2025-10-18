from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

def encrypt_message(message, key):
    """
    Criptează un mesaj folosind cheia AES
    """
    try:
        # Convertim cheia în format potrivit pentru Fernet
        # Fernet necesită o cheie de 32 bytes (256 bits)
        if len(key) < 32:
            # Padding cu zerouri dacă cheia este prea scurtă
            key = key + b'\x00' * (32 - len(key))
        elif len(key) > 32:
            # Truncăm dacă cheia este prea lungă
            key = key[:32]
        
        # Encodăm cheia în base64 pentru Fernet
        key_b64 = base64.urlsafe_b64encode(key)
        
        # Creez obiectul Fernet pentru criptare
        f = Fernet(key_b64)
        
        # Criptez mesajul
        encrypted_message = f.encrypt(message.encode())
        
        return encrypted_message
    except Exception as e:
        print(f"Eroare la criptare: {e}")
        return None

def decrypt_message(encrypted_message, key):
    """
    Decriptează un mesaj folosind cheia AES
    """
    try:
        # Convertim cheia în format potrivit pentru Fernet
        if len(key) < 32:
            key = key + b'\x00' * (32 - len(key))
        elif len(key) > 32:
            key = key[:32]
        
        # Encodăm cheia în base64 pentru Fernet
        key_b64 = base64.urlsafe_b64encode(key)
        
        # Creez obiectul Fernet pentru decriptare
        f = Fernet(key_b64)
        
        # Decriptez mesajul
        decrypted_message = f.decrypt(encrypted_message)
        
        return decrypted_message.decode()
    except Exception as e:
        print(f"Eroare la decriptare: {e}")
        return None

def generate_key_from_bb84(bb84_key):
    """
    Generează o cheie AES din cheia BB84
    """
    # Convertim cheia BB84 în bytes
    key_bits = ''.join(map(str, bb84_key))
    
    # Padding pentru a ajunge la 128 bits (16 bytes)
    while len(key_bits) < 128:
        key_bits += '0'
    
    key_bits = key_bits[:128]
    
    # Convertim în bytes
    key_bytes = []
    for i in range(0, 128, 8):
        byte_bits = key_bits[i:i+8]
        key_bytes.append(int(byte_bits, 2))
    
    return bytes(key_bytes)
