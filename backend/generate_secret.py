"""
セキュアなシークレットキーを生成するスクリプト
"""
import secrets
import string

def generate_secret_key(length=64):
    """セキュアなシークレットキーを生成"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return secret_key

if __name__ == "__main__":
    secret_key = generate_secret_key(64)
    print("=" * 80)
    print("生成されたシークレットキー:")
    print("=" * 80)
    print(secret_key)
    print("=" * 80)
    print("\nこのキーを .env ファイルの SECRET_KEY に設定してください")
















