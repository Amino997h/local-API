import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DESKTOP = Path(os.path.expanduser(r"~\OneDrive\Desktop"))
if not DESKTOP.exists():
    DESKTOP = Path(os.path.expanduser(r"~\Desktop"))

PROFILE_DIR = DESKTOP / "chatgpt_profile"
CHATGPT_URL = "https://chatgpt.com/"

# API Server Settings
HOST = "127.0.0.1"
PORT = 8008
API_KEY = os.getenv("CHATGPT_API_KEY", "sk-chatgpt-local-secret-key")

# Timeouts (in seconds/ms)
TIMEOUT_MS = 60000
RESPONSE_TIMEOUT_SECONDS = 120
RETRY_TIMEOUT_SECONDS = 30
MAX_EXTRACTION_ATTEMPTS = 3

# Playwright Selectors
PROMPT_SELECTORS = [
    "#prompt-textarea",
    'div[id="prompt-textarea"]',
    'div[contenteditable="true"][role="textbox"]',
    'div[contenteditable="true"]',
    "textarea",
]

SEND_BUTTON_SELECTORS = [
    'button[data-testid="send-button"]',
    'button[aria-label*="Send"]',
    'button[aria-label*="إرسال"]',
]

STOP_SELECTORS = [
    'button[data-testid="stop-button"]',
    'button[aria-label*="Stop"]',
    'button[aria-label*="إيقاف"]',
]

COPY_BUTTON_SELECTORS = [
    'button[aria-label*="Copy"]',
    'button[aria-label*="نسخ"]',
    'button[data-testid*="copy"]',
]
