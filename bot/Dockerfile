# ─── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Installer les dépendances dans un venv isolé
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copier les dépendances depuis le builder
COPY --from=builder /install /usr/local

# Copier le code source
COPY main.py .

# Utilisateur non-root pour la sécurité
RUN useradd -m botuser
USER botuser

CMD ["python", "-u", "main.py"]
