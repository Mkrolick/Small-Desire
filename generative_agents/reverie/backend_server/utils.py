import os


def _load_dotenv(path=None):
    """Load KEY=VALUE pairs from a .env into os.environ (without overriding
    already-set vars). Dependency-free; defaults to the repo-root .env located
    relative to this file so it works regardless of CWD."""
    if path is None:
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

# --- Legacy config (paths are relative to reverie/backend_server) ---
openai_api_key = "unused"          # legacy global; kept so imports don't break
key_owner = "SmallDesire"
maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"
fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"
collision_block_id = "32125"
debug = True

# --- SmallDesire provider config (read from env; safe local defaults) ---
TOKENSPLS_BASE_URL = os.environ.get("TOKENSPLS_BASE_URL", "http://127.0.0.1:8000/v1")
TOKENSPLS_MODEL = os.environ.get("TOKENSPLS_MODEL", "gpt-5.4")
TOKENSPLS_API_KEY = os.environ.get("TOKENSPLS_API_KEY", "sk-noauth")
EMBED_BASE_URL = os.environ.get("EMBED_BASE_URL", "https://api.openai.com/v1")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
# Accept the explicit EMBED_API_KEY, or fall back to common OpenAI key names
# (the project's .env uses OPEN_AI_KEY) so embeddings "just work" from .env.
EMBED_API_KEY = (os.environ.get("EMBED_API_KEY")
                 or os.environ.get("OPEN_AI_KEY")
                 or os.environ.get("OPENAI_API_KEY")
                 or "")
