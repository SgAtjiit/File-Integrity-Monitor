import rsa_manual
import cipher_manual
import os

def test_rsa():
    print("\n--- Testing Manual RSA ---")
    
    # 1. Key Generation
    print("Generating keys...")
    pub, priv = rsa_manual.generate_keypair(keysize=512) # Small size for speed
    print(f"Public Key: {pub}")
    print(f"Private Key: {priv}")
    
    # 2. Sign & Verify
    message = "This is a secure baseline."
    print(f"Signing message: '{message}'")
    signature = rsa_manual.sign(message, priv)
    print(f"Signature: {signature}")
    
    print("Verifying signature...")
    valid = rsa_manual.verify(message, signature, pub)
    if valid:
        print("SUCCESS: Signature verified.")
    else:
        print("FAILED: Signature invalid.")
        exit(1)
        
    # 3. Tamper Test
    print("Verifying tampered message...")
    valid = rsa_manual.verify(message + "tampered", signature, pub)
    if not valid:
        print("SUCCESS: Tampering detected.")
    else:
        print("FAILED: Tampering NOT detected.")
        exit(1)

def test_caesar():
    print("\n--- Testing Manual Caesar Cipher ---")
    
    text = "Hello World! 123"
    shift = 3
    
    # 1. Encrypt
    encrypted = cipher_manual.caesar_encrypt(text, shift)
    print(f"Original:  {text}")
    print(f"Encrypted: {encrypted}")
    
    if encrypted == "Khoor Zruog! 123":
        print("SUCCESS: Encryption correct.")
    else:
        print("FAILED: Encryption incorrect.")
        exit(1)
        
    # 2. Decrypt
    decrypted = cipher_manual.caesar_decrypt(encrypted, shift)
    print(f"Decrypted: {decrypted}")
    
    if decrypted == text:
        print("SUCCESS: Decryption correct.")
    else:
        print("FAILED: Decryption incorrect.")
        exit(1)

if __name__ == "__main__":
    test_rsa()
    test_caesar()
