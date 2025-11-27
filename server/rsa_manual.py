import random
import hashlib
import os

# --- Math Primitives ---

def gcd(a, b):
    """Euclidean algorithm for GCD."""
    while b:
        a, b = b, a % b
    return a

def extended_gcd(a, b):
    """Extended Euclidean Algorithm. Returns (g, x, y) such that ax + by = g."""
    if a == 0:
        return b, 0, 1
    else:
        g, y, x = extended_gcd(b % a, a)
        return g, x - (b // a) * y, y

def modinv(a, m):
    """Modular multiplicative inverse."""
    g, x, y = extended_gcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

def is_prime(n, k=5):
    """Miller-Rabin primality test."""
    if n == 2 or n == 3: return True
    if n < 2 or n % 2 == 0: return False

    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def generate_prime(bits=1024):
    """Generates a large prime number."""
    while True:
        # Generate a random odd number
        n = random.getrandbits(bits)
        if n % 2 == 0: 
            n += 1
        if is_prime(n):
            return n

# --- RSA Functions ---

def generate_keypair(keysize=1024):
    """Generates RSA public and private keys."""
    print(f"Generating {keysize}-bit RSA keys (this may take a moment)...")
    
    e = 65537
    
    # Generate p and q such that gcd(e, phi) = 1
    while True:
        p = generate_prime(keysize // 2)
        q = generate_prime(keysize // 2)
        phi = (p - 1) * (q - 1)
        if gcd(e, phi) == 1:
            break
            
    n = p * q
    d = modinv(e, phi)
    
    # Public key: (e, n), Private key: (d, n)
    return ((e, n), (d, n))

def encrypt(pk, plaintext_int):
    """Encrypts an integer using public key (e, n)."""
    e, n = pk
    # c = m^e mod n
    return pow(plaintext_int, e, n)

def decrypt(pk, ciphertext_int):
    """Decrypts an integer using private key (d, n)."""
    d, n = pk
    # m = c^d mod n
    return pow(ciphertext_int, d, n)

# --- Digital Signature Wrappers ---

def sign(message, private_key):
    """Signs a message (string) using the private key."""
    # 1. Hash the message
    msg_hash = hashlib.sha256(message.encode()).hexdigest()
    # 2. Convert hash to integer
    hash_int = int(msg_hash, 16)
    # 3. "Decrypt" the hash with private key to sign
    signature_int = decrypt(private_key, hash_int)
    return hex(signature_int)[2:]

def verify(message, signature_hex, public_key):
    """Verifies a signature for a message using the public key."""
    try:
        # 1. Hash the message
        msg_hash = hashlib.sha256(message.encode()).hexdigest()
        hash_int = int(msg_hash, 16)
        
        # 2. "Encrypt" the signature with public key to reveal original hash
        signature_int = int(signature_hex, 16)
        decrypted_hash_int = encrypt(public_key, signature_int)
        
        # 3. Compare
        return hash_int == decrypted_hash_int
    except Exception as e:
        print(f"Verification error: {e}")
        return False

# --- Key Storage ---

def save_keys(public_key, private_key, pub_file="public_key.txt", priv_file="private_key.txt"):
    with open(pub_file, "w") as f:
        f.write(f"{public_key[0]},{public_key[1]}")
    with open(priv_file, "w") as f:
        f.write(f"{private_key[0]},{private_key[1]}")

def load_keys(pub_file="public_key.txt", priv_file="private_key.txt"):
    try:
        with open(pub_file, "r") as f:
            e, n = map(int, f.read().split(","))
            pub = (e, n)
        with open(priv_file, "r") as f:
            d, n = map(int, f.read().split(","))
            priv = (d, n)
        return pub, priv
    except FileNotFoundError:
        return None, None
