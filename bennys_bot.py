# Benny-s-bot-
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import pytz

# ─────────────────────────────────────────────
#  CONFIG — remplace par tes vraies valeurs
# ─────────────────────────────────────────────
import os
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1466949609501888523         # ID de ton serveur (int)
LOG_CHANNEL_ID = 1491892374551658516    # Salon où les contrats signés sont loggés (optionnel)

# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

TZ = pytz.timezone("Europe/Paris")


# ══════════════════════════════════════════════
#  HELPER — construit l'embed du contrat
# ══════════════════════════════════════════════
def build_embed(
    entreprise: str,
    representant: str,
    offre_bennys: str,
    offre_partenaire: str,
    expiration_str: str,
    signe_par: str,
    statut: str = "🟡 En attente de signature",
    color: int = 0xF5A623,
) -> discord.Embed:
    embed = discord.Embed(title="🤝 Contrat de Partenariat", color=color)
    embed.add_field(name="🏢 Entreprise",        value=entreprise,       inline=False)
    embed.add_field(name="👤 Représentant",      value=representant,     inline=False)
    embed.add_field(name="🍔 Offre Benny's",     value=offre_bennys,     inline=False)
    embed.add_field(name="📦 Offre Partenaire",  value=offre_partenaire, inline=False)
    embed.add_field(name="⏳ Expiration",         value=expiration_str,   inline=False)
    embed.add_field(name="✍️ Initié par",         value=signe_par,        inline=False)
    embed.add_field(name="📌 Statut",             value=statut,           inline=False)
    embed.set_footer(text="Benny's • Excellence")
    embed.timestamp = datetime.now(TZ)
    return embed


# ══════════════════════════════════════════════
#  MODAL — Renouvellement (nouvelle durée)
# ══════════════════════════════════════════════
class RenouvellementModal(discord.ui.Modal, title="🔄 Renouveler le contrat"):
    duree_jours = discord.ui.TextInput(
        label="⏳ Nouvelle durée (en jours)",
        placeholder="Ex: 7",
        required=True,
        max_length=3,
    )

    def __init__(self, original_embed: discord.Embed):
        super().__init__()
        self.original_embed = original_embed

    async def on_submit(self, interaction: discord.Interaction):
        try:
            jours = int(self.duree_jours.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ La durée doit être un nombre entier.", ephemeral=True
            )
            return

        now = datetime.now(TZ)
        expiration = now + timedelta(days=jours)
        expiration_str = expiration.strftime("%A %d %B %Y at %H:%M")

        # Récupère les champs de l'embed original
        fields = {f.name: f.value for f in self.original_embed.fields}

        new_embed = build_embed(
            entreprise=fields.get("🏢 Entreprise", "—"),
            representant=fields.get("👤 Représentant", "—"),
            offre_bennys=fields.get("🍔 Offre Benny's", "—"),
            offre_partenaire=fields.get("📦 Offre Partenaire", "—"),
            expiration_str=expiration_str,
            signe_par=fields.get("✍️ Initié par", "—"),
            statut=f"🔄 Renouvelé par {interaction.user.mention}",
            color=0x3498DB,
        )

        view = ContratView()
        await interaction.response.edit_message(embed=new_embed, view=view)

        # Log
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = new_embed.copy()
            log_embed.title = "📋 [LOG] Contrat Renouvelé"
            await log_channel.send(embed=log_embed)


# ══════════════════════════════════════════════
#  VIEW — Les 3 boutons
# ══════════════════════════════════════════════
class ContratView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistant (même après redémarrage si custom_id fixe)

    # ── Bouton SIGNÉ ──
    @discord.ui.button(
        label="✅ Signé",
        style=discord.ButtonStyle.success,
        custom_id="contrat:signe",
    )
    async def signe(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        fields = {f.name: f.value for f in embed.fields}

        new_embed = build_embed(
            entreprise=fields.get("🏢 Entreprise", "—"),
            representant=fields.get("👤 Représentant", "—"),
            offre_bennys=fields.get("🍔 Offre Benny's", "—"),
            offre_partenaire=fields.get("📦 Offre Partenaire", "—"),
            expiration_str=fields.get("⏳ Expiration", "—"),
            signe_par=fields.get("✍️ Initié par", "—"),
            statut=f"✅ Signé par {interaction.user.mention}",
            color=0x2ECC71,
        )

        # Désactive le bouton Signé après signature
        for child in self.children:
            if child.custom_id == "contrat:signe":
                child.disabled = True

        await interaction.response.edit_message(embed=new_embed, view=self)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = new_embed.copy()
            log_embed.title = "📋 [LOG] Contrat Signé"
            await log_channel.send(embed=log_embed)

    # ── Bouton RENOUVELÉ ──
    @discord.ui.button(
        label="🔄 Renouvelé",
        style=discord.ButtonStyle.primary,
        custom_id="contrat:renouvele",
    )
    async def renouvele(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        modal = RenouvellementModal(original_embed=embed)
        await interaction.response.send_modal(modal)

    # ── Bouton CLÔTURER ──
    @discord.ui.button(
        label="🔴 Clôturer",
        style=discord.ButtonStyle.danger,
        custom_id="contrat:cloture",
    )
    async def cloture(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        fields = {f.name: f.value for f in embed.fields}

        new_embed = build_embed(
            entreprise=fields.get("🏢 Entreprise", "—"),
            representant=fields.get("👤 Représentant", "—"),
            offre_bennys=fields.get("🍔 Offre Benny's", "—"),
            offre_partenaire=fields.get("📦 Offre Partenaire", "—"),
            expiration_str=fields.get("⏳ Expiration", "—"),
            signe_par=fields.get("✍️ Initié par", "—"),
            statut=f"🔴 Clôturé par {interaction.user.mention}",
            color=0xE74C3C,
        )

        # Désactive tous les boutons après clôture
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=new_embed, view=self)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = new_embed.copy()
            log_embed.title = "📋 [LOG] Contrat Clôturé"
            await log_channel.send(embed=log_embed)


# ══════════════════════════════════════════════
#  MODAL — Formulaire de création
# ══════════════════════════════════════════════
class ContratModal(discord.ui.Modal, title="📝 Contrat de Partenariat — Benny's"):

    entreprise = discord.ui.TextInput(
        label="🏢 Entreprise",
        placeholder="Nom de l'entreprise partenaire",
        required=True,
        max_length=50,
    )
    representant = discord.ui.TextInput(
        label="👤 Représentant (mention ou pseudo)",
        placeholder="Ex: @Sublab.",
        required=True,
        max_length=50,
    )
    offre_bennys = discord.ui.TextInput(
        label="🍔 Offre Benny's",
        placeholder="Ex: 50 Menu Street Classic",
        required=True,
        max_length=100,
    )
    offre_partenaire = discord.ui.TextInput(
        label="📦 Offre Partenaire",
        placeholder="Ex: 50 Kit Réparation + Réparation + Lavage Gratuit",
        required=True,
        max_length=200,
    )
    duree_jours = discord.ui.TextInput(
        label="⏳ Durée du contrat (en jours)",
        placeholder="Ex: 7",
        required=True,
        max_length=3,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            jours = int(self.duree_jours.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ La durée doit être un nombre entier (ex: 7).", ephemeral=True
            )
            return

        now = datetime.now(TZ)
        expiration = now + timedelta(days=jours)
        expiration_str = expiration.strftime("%A %d %B %Y at %H:%M")

        embed = build_embed(
            entreprise=self.entreprise.value,
            representant=self.representant.value,
            offre_bennys=self.offre_bennys.value,
            offre_partenaire=self.offre_partenaire.value,
            expiration_str=expiration_str,
            signe_par=interaction.user.mention,
            statut="🟡 En attente de signature",
            color=0xF5A623,
        )

        view = ContratView()
        await interaction.response.send_message(embed=embed, view=view)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = embed.copy()
            log_embed.title = "📋 [LOG] Nouveau Contrat créé"
            await log_channel.send(embed=log_embed)


# ══════════════════════════════════════════════
#  COMMANDE SLASH — /contrat
# ══════════════════════════════════════════════
@tree.command(
    name="contrat",
    description="Créer un contrat de partenariat Benny's",
)
async def contrat(interaction: discord.Interaction):
    await interaction.response.send_modal(ContratModal())


# ══════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════
@bot.event
async def on_ready():
    # Enregistre la vue persistante pour que les boutons fonctionnent après redémarrage
    bot.add_view(ContratView())

    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print(f"✅ Bot connecté en tant que {bot.user} | Commandes sync sur le serveur {GUILD_ID}")


# ══════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════
bot.run(TOKEN)
