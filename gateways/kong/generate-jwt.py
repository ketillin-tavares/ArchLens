"""Gera um JWT válido para testar as APIs via Kong."""

import datetime
import sys

import jwt


SECRET: str = sys.argv[1] if len(sys.argv) > 1 else "archlens-jwt-secret-dev"
EXPIRY_HOURS: int = int(sys.argv[2]) if len(sys.argv) > 2 else 1


def build_payload(expiry_hours: int) -> dict:
    """Constrói o payload do token JWT com as claims necessárias.

    Args:
        expiry_hours: Número de horas até o token expirar.

    Returns:
        Dicionário com as claims do JWT.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "iss": "archlens-issuer",
        "sub": "archlens-client",
        "role": "admin",
        "iat": now,
        "exp": now + datetime.timedelta(hours=expiry_hours),
    }


def generate_token(secret: str, expiry_hours: int) -> str:
    """Assina e retorna o token JWT.

    Args:
        secret: Segredo HS256 configurado no Kong consumer.
        expiry_hours: Tempo de vida do token em horas.

    Returns:
        String do token JWT assinado.
    """
    payload = build_payload(expiry_hours)
    return jwt.encode(payload, secret, algorithm="HS256")


if __name__ == "__main__":
    token = generate_token(SECRET, EXPIRY_HOURS)
    sys.stdout.write(token + "\n")
