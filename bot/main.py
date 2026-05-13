import discord
from discord import app_commands
import aiohttp
import asyncio
import os
import logging

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
TOKEN            = os.getenv("DISCORD_TOKEN")
OLLAMA_PRIMARY   = os.getenv("OLLAMA_PRIMARY_URL", "http://ollama-main:11434")
OLLAMA_BACKUP    = os.getenv("OLLAMA_BACKUP_URL", "")
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT   = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# ─── Catégories disponibles pour l'autocomplete ───────────────────────────────
CATEGORIES = [
    "Action-RPG", "FPS", "Stratégie au tour par tour", "Aventure",
    "Sport", "Simulation", "Horreur", "Plateforme", "MMORPG",
    "Indie", "Course", "Combat", "Puzzle", "Survie", "Bac-à-sable",
    "Visual Novel", "Roguelite", "Beat them all", "Tactical RPG",
]

# ─── Prompt système ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "Tu es GameBot, un expert en jeux vidéo passionné et enthousiaste. "
    "Tu réponds toujours en français, de manière concise et utile. "
    "Tu couvres tous les genres et toutes les plateformes (PC, PS5, Xbox, Switch, etc.). "
    "Pour chaque recommandation, tu mentionnes le titre, la plateforme principale "
    "et un argument accrocheur en 1 à 2 phrases max."
)

# ─── Client Discord ────────────────────────────────────────────────────────────
class GameBotClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        await self.tree.sync()
        log.info("Commandes slash synchronisées.")

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await super().close()

    async def on_ready(self) -> None:
        log.info(f"Connecté en tant que {self.user} | Modèle : {OLLAMA_MODEL}")
        await self.change_presence(
            activity=discord.Game(name="Expert Gaming 🎮 | /recommande")
        )


client = GameBotClient()


# ─── Appel Ollama avec fallback ────────────────────────────────────────────────
async def ask_ollama(prompt: str) -> str:
    servers = [s for s in [OLLAMA_PRIMARY, OLLAMA_BACKUP] if s]

    for url in servers:
        try:
            log.info(f"Requête vers {url}...")
            async with client.session.post(
                f"{url}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                    "stream": False,
                },
                timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "Erreur : réponse vide du modèle.")
                log.warning(f"HTTP {resp.status} depuis {url}")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.warning(f"Serveur {url} injoignable : {e}")
            continue

    return (
        "⚠️ Aucun serveur Ollama n'est disponible pour le moment.\n"
        "Réessaie dans quelques instants !"
    )


# ─── Commande /recommande ─────────────────────────────────────────────────────
@client.tree.command(
    name="recommande",
    description="Obtiens 3 recommandations de jeux par catégorie"
)
@app_commands.describe(
    categorie="La catégorie de jeux (ex : FPS, RPG, Horreur…)"
)
async def recommande(interaction: discord.Interaction, categorie: str) -> None:
    await interaction.response.defer()

    prompt = (
        f"Recommande exactement 3 jeux dans la catégorie : {categorie}. "
        "Pour chaque jeu, donne le titre, la plateforme principale et un argument "
        "accrocheur en 1 à 2 phrases max. Format numéroté : 1. 2. 3."
    )
    reponse = await ask_ollama(prompt)

    embed = discord.Embed(
        title=f"🎮 Top 3 — {categorie}",
        description=reponse,
        color=discord.Color.purple(),
    )
    embed.set_footer(text=f"Propulsé par Ollama • Modèle : {OLLAMA_MODEL}")
    await interaction.followup.send(embed=embed)


@recommande.autocomplete("categorie")
async def categorie_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=cat, value=cat)
        for cat in CATEGORIES
        if current.lower() in cat.lower()
    ][:25]


# ─── Commande /comparatif ─────────────────────────────────────────────────────
@client.tree.command(
    name="comparatif",
    description="Compare deux jeux côte à côte"
)
@app_commands.describe(
    jeu1="Premier jeu à comparer",
    jeu2="Deuxième jeu à comparer"
)
async def comparatif(
    interaction: discord.Interaction, jeu1: str, jeu2: str
) -> None:
    await interaction.response.defer()

    prompt = (
        f"Compare '{jeu1}' et '{jeu2}'. "
        "Pour chaque jeu, donne 2 points forts et 1 point faible en 1 phrase chacun. "
        "Conclus avec lequel est le meilleur selon le profil du joueur."
    )
    reponse = await ask_ollama(prompt)

    embed = discord.Embed(
        title=f"⚖️ {jeu1}  vs  {jeu2}",
        description=reponse,
        color=discord.Color.gold(),
    )
    embed.set_footer(text=f"Propulsé par Ollama • Modèle : {OLLAMA_MODEL}")
    await interaction.followup.send(embed=embed)


# ─── Commande /conseil ────────────────────────────────────────────────────────
@client.tree.command(
    name="conseil",
    description="Pose une question sur un jeu spécifique"
)
@app_commands.describe(
    jeu="Le jeu dont tu veux parler",
    question="Ta question sur ce jeu"
)
async def conseil(
    interaction: discord.Interaction, jeu: str, question: str
) -> None:
    await interaction.response.defer()

    prompt = f"Concernant le jeu '{jeu}' : {question}. Réponds de manière concise et utile."
    reponse = await ask_ollama(prompt)

    embed = discord.Embed(
        title=f"🕹️ {jeu}",
        description=reponse,
        color=discord.Color.green(),
    )
    embed.set_footer(text=f"Propulsé par Ollama • Modèle : {OLLAMA_MODEL}")
    await interaction.followup.send(embed=embed)


# ─── Lancement ────────────────────────────────────────────────────────────────
if not TOKEN:
    raise ValueError("La variable d'environnement DISCORD_TOKEN est manquante !")

client.run(TOKEN, log_handler=None)
