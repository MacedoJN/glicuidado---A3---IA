import hashlib
import secrets


def gerar_hash_senha(senha, salt=None):
    """
    Gera um hash seguro da senha usando PBKDF2-HMAC-SHA256.
    Retorna a string no formato 'salt$hash' para armazenar no banco.
    """

    if salt is None:
        salt = secrets.token_hex(16)

    hash_obj = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    )

    return f"{salt}${hash_obj.hex()}"


def verificar_senha(senha, senha_hash_armazenada):
    """Verifica se a senha informada corresponde ao hash armazenado."""

    try:
        salt, _ = senha_hash_armazenada.split("$")
    except ValueError:
        return False

    novo_hash = gerar_hash_senha(senha, salt)

    return secrets.compare_digest(novo_hash, senha_hash_armazenada)
