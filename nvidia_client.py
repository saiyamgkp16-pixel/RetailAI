"""
nvidia_client.py - NVIDIA NIM Hosted API Client via OpenAI SDK
Part of RetailPulse AI

Connects to NVIDIA NIM endpoints hosted on the NVIDIA API Catalog (OpenAI-compatible)
with graceful fallback, error handling, and zero-crash guarantees when offline.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration constants
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"


def get_nvidia_config() -> Dict[str, str]:
    """
    Retrieve configured NVIDIA NIM environment parameters.
    Never exposes raw secrets; checks for placeholder strings.
    """
    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    model = os.environ.get("NVIDIA_MODEL", DEFAULT_MODEL).strip()
    base_url = os.environ.get("NVIDIA_BASE_URL", DEFAULT_BASE_URL).strip()
    
    # Check if key is empty or still holds sample placeholder
    is_placeholder = api_key in [
        "",
        "your_api_key_here",
        "your_nvidia_api_key_here",
        "nvapi-placeholder"
    ]
    
    return {
        "api_key": api_key,
        "model": model if model else DEFAULT_MODEL,
        "base_url": base_url if base_url else DEFAULT_BASE_URL,
        "is_configured": not is_placeholder and len(api_key) > 10
    }


def ask_nvidia(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.2
) -> Dict[str, Any]:
    """
    Execute a chat completion call to NVIDIA NIM hosted API.
    
    Guarantees:
    - Never crashes the caller if network, auth, or model fails.
    - Returns structured response with success flag and error details.
    """
    config = get_nvidia_config()
    
    if not config["is_configured"]:
        return {
            "success": False,
            "content": "",
            "model": config["model"],
            "error": "NVIDIA_API_KEY is not configured or contains placeholder. Operating in local fallback mode.",
            "fallback_used": True
        }
        
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
            timeout=15.0  # Safe timeout to prevent UI hang
        )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=config["model"],
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content or ""
        return {
            "success": True,
            "content": content.strip(),
            "model": config["model"],
            "error": None,
            "fallback_used": False
        }
        
    except Exception as e:
        err_msg = str(e)
        return {
            "success": False,
            "content": "",
            "model": config["model"],
            "error": f"NVIDIA API Error: {err_msg}",
            "fallback_used": True
        }


def check_nvidia_connection() -> Dict[str, Any]:
    """
    Perform a lightweight ping to verify NVIDIA NIM API connectivity.
    """
    config = get_nvidia_config()
    if not config["is_configured"]:
        return {
            "connected": False,
            "message": "NVIDIA API key not configured. Local fallback engine is active.",
            "model": config["model"]
        }
        
    res = ask_nvidia("Say 'RetailPulse AI connected' in 4 words.", max_tokens=15, temperature=0.0)
    if res["success"]:
        return {
            "connected": True,
            "message": f"NVIDIA NIM connected successfully using model: {res['model']}",
            "model": res["model"]
        }
    else:
        return {
            "connected": False,
            "message": f"NVIDIA NIM unavailable ({res['error']}). Local fallback engine active.",
            "model": config["model"]
        }
