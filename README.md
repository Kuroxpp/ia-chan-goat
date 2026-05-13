# 🎮 GameBot Discord — Expert en jeux vidéo

Bot Discord alimenté par **Ollama** (LLM local) qui recommande des jeux par catégorie, compare des titres et répond à des questions gaming.

---

## Structure du projet

```
mon-bot-gaming/
├── bot/
│   ├── main.py           # Code du bot (3 commandes slash)
│   ├── requirements.txt  # discord.py, aiohttp
│   └── Dockerfile        # Image Python slim multi-stage
├── docker-compose.yml    # Orchestration (bot + ollama-main)
├── .env.example          # Template des variables d'environnement
├── .env                  # Tes secrets (NON commité dans Git)
├── .gitignore
└── README.md
```

---

## Commandes Discord

| Commande | Description |
|---|---|
| `/recommande <categorie>` | 3 recommandations dans une catégorie (avec autocomplete) |
| `/comparatif <jeu1> <jeu2>` | Comparaison côte à côte de deux jeux |
| `/conseil <jeu> <question>` | Réponse à une question sur un jeu précis |

---

## Prérequis

- Docker + Docker Compose v2
- **NVIDIA Container Toolkit** installé sur l'hôte (pour le GPU)
- Un bot Discord créé sur [discord.com/developers](https://discord.com/developers)
- Un serveur backup Ollama accessible sur le réseau (optionnel mais recommandé)

---

## Installation rapide

### 1. Cloner le dépôt

```bash
git clone https://github.com/TON_USER/mon-bot-gaming.git
cd mon-bot-gaming
```

### 2. Créer le fichier `.env`

```bash
cp .env.example .env
```

Édite `.env` avec tes valeurs :

```env
DISCORD_TOKEN=ton_token_discord_ici
OLLAMA_BACKUP_URL=http://192.168.1.XXX:11434
OLLAMA_MODEL=llama3
```

### 3. Lancer la stack

```bash
docker compose up -d --build
```

### 4. Télécharger le modèle sur Ollama

```bash
docker exec -it ollama-main ollama pull llama3
```

Et sur ton serveur backup (si applicable) :

```bash
ollama pull llama3
```

### 5. Vérifier que le bot est en ligne

```bash
docker compose logs -f bot-gaming
```

---

## Déploiement via Portainer

### Méthode 1 — Stack depuis un dépôt Git (recommandée)

1. Dans Portainer → **Stacks** → **Add stack**
2. Choisir **Repository**
3. Renseigner l'URL de ton dépôt Git
4. Fichier de composition : `docker-compose.yml`
5. Dans **Environment variables**, ajouter :
   - `DISCORD_TOKEN` = ton token
   - `OLLAMA_BACKUP_URL` = `http://IP_BACKUP:11434`
   - `OLLAMA_MODEL` = `llama3`
6. Cliquer **Deploy the stack**

> Portainer peut détecter les mises à jour du dépôt automatiquement si tu actives **Auto update** avec un webhook ou un polling interval.

### Méthode 2 — Upload du docker-compose.yml

1. Dans Portainer → **Stacks** → **Add stack**
2. Choisir **Upload**
3. Uploader le fichier `docker-compose.yml`
4. Renseigner les variables d'environnement comme ci-dessus

---

## Architecture réseau

```
Discord API
    │
    ▼
bot-gaming (container)
    │
    ├──► ollama-main:11434  (container local, GPU Nvidia)
    │
    └──► OLLAMA_BACKUP_URL  (serveur externe, CPU)
```

Le bot essaie toujours le serveur **principal** en premier. En cas d'échec (timeout, erreur réseau), il bascule automatiquement sur le **backup**.

---

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `DISCORD_TOKEN` | — | **Obligatoire.** Token du bot Discord |
| `OLLAMA_PRIMARY_URL` | `http://ollama-main:11434` | URL du serveur Ollama principal |
| `OLLAMA_BACKUP_URL` | _(vide)_ | URL du serveur Ollama backup (IP externe) |
| `OLLAMA_MODEL` | `llama3` | Modèle Ollama à utiliser |
| `OLLAMA_TIMEOUT` | `60` | Timeout en secondes par requête |

---

## Mise à jour du bot

```bash
git pull
docker compose up -d --build bot-gaming
```

Avec Portainer (méthode Git) : cliquer **Pull and redeploy** ou laisser l'auto-update faire son travail.

---

## Gestion des logs

```bash
# Logs du bot
docker compose logs -f bot-gaming

# Logs Ollama
docker compose logs -f ollama-main

# Tous les services
docker compose logs -f
```
