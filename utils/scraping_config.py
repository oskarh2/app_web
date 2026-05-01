"""
Módulo de configuración global
"""
import os
from datetime import datetime

# Configuración global
HEADLESS_MODE = False

def set_headless_mode(value):
    """Set headless mode globally"""
    global HEADLESS_MODE
    if isinstance(value, bool):
        HEADLESS_MODE = value
    elif isinstance(value, str):
        HEADLESS_MODE = value.lower() in ["true", "yes", "1"]
    else:
        HEADLESS_MODE = bool(value)
    print(f"🖥️ Headless mode set to: {HEADLESS_MODE}")
    return HEADLESS_MODE

def get_headless_mode():
    """Get current headless mode"""
    return HEADLESS_MODE