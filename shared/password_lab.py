import secrets
import string
import math
import hashlib
import base64
import os
import sys
from typing import Dict, Any, List, Optional

try:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class PasswordLabManager:
    """
    Manages Password Lab operations: generation, strength checking, and hashing.
    """

    # A short list of common, distinct words for passphrase generation.
    # In a full implementation, this could be the EFF short wordlist.
    DEFAULT_WORDLIST = [
        "apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew",
        "kiwi", "lemon", "mango", "nectarine", "orange", "papaya", "quince", "raspberry",
        "strawberry", "tangerine", "ugli", "vanilla", "watermelon", "xigua", "yellow", "zucchini",
        "bird", "cat", "dog", "fish", "horse", "cow", "pig", "sheep", "goat", "chicken",
        "duck", "goose", "turkey", "mouse", "rat", "rabbit", "hare", "squirrel", "chipmunk",
        "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "black", "white",
        "circle", "square", "triangle", "rectangle", "oval", "star", "heart", "diamond",
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "sun", "moon", "star", "planet", "comet", "asteroid", "meteor", "galaxy", "universe",
        "ocean", "sea", "river", "lake", "pond", "stream", "creek", "brook", "waterfall",
        "mountain", "hill", "valley", "canyon", "cliff", "cave", "volcano", "island", "peninsula",
        "tree", "flower", "grass", "bush", "shrub", "vine", "fern", "moss", "lichen",
        "car", "truck", "bus", "train", "plane", "boat", "ship", "submarine", "bicycle"
    ]

    def generate_passphrase(self, words: int = 4, separator: str = "-") -> str:
        """
        Generates a passphrase consisting of randomly chosen words.
        """
        if words < 1:
            raise ValueError("Passphrase must contain at least 1 word.")

        chosen_words = [secrets.choice(self.DEFAULT_WORDLIST) for _ in range(words)]
        return separator.join(chosen_words)

    def generate(self, length: int = 16, use_upper: bool = True, use_lower: bool = True, use_digits: bool = True, use_symbols: bool = True) -> str:
        """
        Generates a cryptographically secure random password.
        """
        if length < 4:
            raise ValueError("Password length must be at least 4.")

        charset = ""
        if use_upper: charset += string.ascii_uppercase
        if use_lower: charset += string.ascii_lowercase
        if use_digits: charset += string.digits
        if use_symbols: charset += string.punctuation

        if not charset:
            raise ValueError("At least one character set must be selected.")

        # Ensure at least one character from each selected set is included
        password_chars = []
        if use_upper: password_chars.append(secrets.choice(string.ascii_uppercase))
        if use_lower: password_chars.append(secrets.choice(string.ascii_lowercase))
        if use_digits: password_chars.append(secrets.choice(string.digits))
        if use_symbols: password_chars.append(secrets.choice(string.punctuation))

        # Fill the rest
        remaining_length = length - len(password_chars)
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(charset))

        # Shuffle the result
        password_list = list(password_chars)
        # shuffle doesn't exist in secrets, use SystemRandom which secrets uses
        # or just use random.shuffle if we don't care about order leakage (which we shouldn't for password generation usually, but let's be safe)
        # Actually secrets module suggests using SystemRandom().shuffle if needed, or just manual shuffle.
        # But random.shuffle uses Mersenne Twister, not CSPRNG.
        # A simple fisher-yates using secrets.randbelow is better.
        for i in range(len(password_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_list[i], password_list[j] = password_list[j], password_list[i]

        return "".join(password_list)

    def check_strength(self, password: str) -> Dict[str, Any]:
        """
        Analyzes password strength using entropy calculation and heuristics.
        """
        length = len(password)

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in string.punctuation for c in password)

        pool_size = 0
        if has_lower: pool_size += 26
        if has_upper: pool_size += 26
        if has_digit: pool_size += 10
        if has_symbol: pool_size += 32

        if pool_size == 0:
            entropy = 0
        else:
            entropy = length * math.log2(pool_size)

        # Score (0-4)
        score = 0
        if entropy > 28: score += 1
        if entropy > 40: score += 1
        if entropy > 60: score += 1
        if entropy > 100: score += 1 # Bonus for very strong

        feedback = []
        if length < 8:
            feedback.append("Password is too short.")
            score = min(score, 1) # Cap score for short passwords
        if not (has_upper and has_lower and has_digit):
            feedback.append("Add more variety (uppercase, lowercase, numbers).")
        if not has_symbol:
            feedback.append("Add symbols for higher entropy.")
        if entropy < 40 and length >= 8:
            feedback.append("Entropy is low, consider a longer password or more variety.")

        # Common word check (very basic)
        common_words = ["password", "123456", "admin", "welcome", "qwerty"]
        if password.lower() in common_words:
            score = 0
            feedback.append("This is a very common password.")

        return {
            "score": score,
            "entropy": round(entropy, 2),
            "feedback": feedback,
            "length": length
        }

    def hash_password(self, password: str, algo: str = "scrypt", salt: Optional[str] = None) -> str:
        """
        Hashes a password.
        """
        if algo == "bcrypt":
            import bcrypt
            if salt:
                salt_bytes = salt.encode('utf-8')
                # bcrypt requires a specific salt format; typically it generates its own.
                # If a custom salt is provided, it might not be a valid bcrypt salt,
                # but we will try to use it if it is 22 characters long base64.
                # However, it's safer to just use gensalt if not a valid bcrypt salt.
                if not salt_bytes.startswith(b"$2"):
                    salt_bytes = bcrypt.gensalt()
            else:
                salt_bytes = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt_bytes)
            return hashed.decode('utf-8')

        if salt:
            salt_bytes = base64.b64decode(salt) if len(salt) % 4 == 0 and salt.endswith("==") or salt.endswith("=") else salt.encode('utf-8')
        else:
            salt_bytes = os.urandom(16)
            salt = base64.b64encode(salt_bytes).decode('utf-8')

        if algo == "scrypt":
            if not HAS_CRYPTOGRAPHY:
                return "Error: 'cryptography' library not installed. Cannot use scrypt."

            kdf = Scrypt(
                salt=salt_bytes,
                length=32,
                n=2**14,
                r=8,
                p=1,
                backend=default_backend()
            )
            key = kdf.derive(password.encode('utf-8'))
            hash_str = base64.b64encode(key).decode('utf-8')
            # Format: $scrypt$salt$hash
            return f"$scrypt${salt}${hash_str}"

        elif algo == "pbkdf2":
            # PBKDF2-HMAC-SHA256
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt_bytes,
                100000
            )
            hash_str = base64.b64encode(key).decode('utf-8')
            return f"$pbkdf2-sha256${salt}${hash_str}"

        else:
            raise ValueError(f"Unsupported algorithm: {algo}")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifies a password against a hash.
        """
        if hashed.startswith("$scrypt$") or hashed.startswith("$pbkdf2-sha256$"):
            parts = hashed.split("$")
            if len(parts) != 4:
                return False
            algo, salt, _ = parts[1], parts[2], parts[3]

            # Map back to algorithm expected by hash_password
            if algo == "pbkdf2-sha256":
                algo = "pbkdf2"

            expected_hash = self.hash_password(password, algo=algo, salt=salt)
            return secrets.compare_digest(expected_hash, hashed)
        elif hashed.startswith("$2a$") or hashed.startswith("$2b$") or hashed.startswith("$2y$"):
            import bcrypt
            try:
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            except Exception:
                return False
        else:
            raise ValueError(f"Unsupported hash format: {hashed}")

def run_password_lab_logic(args):
    """
    Logic for the password-lab command.
    """
    manager = PasswordLabManager()

    if args.action == "generate":
        try:
            pwd = manager.generate(
                length=args.length,
                use_upper=not args.no_upper,
                use_lower=not args.no_lower,
                use_digits=not args.no_digits,
                use_symbols=not args.no_symbols
            )
            print(pwd)
            # Optional: Show strength of generated password
            if args.verbose:
                strength = manager.check_strength(pwd)
                print(f"\nEntropy: {strength['entropy']} bits")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "passphrase":
        try:
            pwd = manager.generate_passphrase(
                words=args.words,
                separator=args.separator
            )
            print(pwd)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "check":
        if not args.password:
            # Prompt securely
            import getpass
            password = getpass.getpass("Enter password to check: ")
        else:
            password = args.password

        result = manager.check_strength(password)

        score_display = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
        score_idx = min(result['score'], 4)

        print(f"--- Password Strength: {score_display[score_idx]} ({result['score']}/4) ---")
        print(f"Length: {result['length']}")
        print(f"Entropy: {result['entropy']} bits")
        if result['feedback']:
            print("Feedback:")
            for item in result['feedback']:
                print(f"  - {item}")

    elif args.action == "hash":
        if not args.password:
            import getpass
            password = getpass.getpass("Enter password to hash: ")
        else:
            password = args.password

        try:
            hashed = manager.hash_password(password, algo=args.algo, salt=args.salt)
            print(hashed)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "verify":
        if not args.password:
            import getpass
            password = getpass.getpass("Enter password to verify: ")
        else:
            password = args.password

        if not getattr(args, 'hash', None):
            print("Error: --hash is required for verify.")
            sys.exit(1)

        try:
            is_valid = manager.verify_password(password, args.hash)
            if is_valid:
                print("✅ Password is valid.")
                sys.exit(0)
            else:
                print("❌ Invalid password.")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
