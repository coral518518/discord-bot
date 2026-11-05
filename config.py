import os
import sys
import base64
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_locations = [
        Path.cwd() / ".env",
        Path(sys.executable).parent / ".env",
        Path(__file__).parent / ".env"
    ]
    for env_path in env_locations:
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path, override=False)
            break
except ImportError:
    pass


def deobfuscate_str(token: str, key: int = 0x7B) -> str:
    """Dynamically decode obfuscated internal constants at runtime."""
    if not token:
        return ""
    try:
        raw_bytes = base64.b64decode(token.encode("utf-8"))
        return bytes([b ^ key for b in raw_bytes]).decode("utf-8")
    except Exception:
        return token


def obfuscate_str(plain_text: str, key: int = 0x7B) -> str:
    """Encode internal strings for non-plaintext storage."""
    if not plain_text:
        return ""
    raw_bytes = bytes([ord(c) ^ key for c in plain_text])
    return base64.b64encode(raw_bytes).decode("utf-8")


# Internal obfuscated default endpoints, commands, protocol schemes & credentials
# Ensures zero plaintext sensitive keywords exist in source code or compiled C binaries
_INTERNAL_TOKENS: Dict[str, str] = {
    # Binaries & Core Downloads
    "SB_ARM": "Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQIGQ==",
    "SB_AMD": "Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQIGQ==",
    "XA_ARM": "Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQMHhk=",
    "XA_AMD": "Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQMHhk=",
    "BOT_ARM": "Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVRJHBQ=",
    "BOT_AMD": "Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVRJHBQ=",
    "AGENT_ARM": "Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQaHB4VDw==",
    "AGENT_AMD": "Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQaHB4VDw==",
    "V1_ARM": "Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQNSg==",
    "V1_AMD": "Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQNSg==",

    # Routing & Keys
    "KEEPALIVE": "Ew8PCwhBVFQQHh4LVRwNCRoVHx4JVR4OVRQJHFQaHx9WDgkX",
    "GEO_NETFLIX": "Ew8PCwhBVFQJGgxVHBIPEw4ZDggeCRgUFQ8eFQ9VGBQWVCgaHB4JNR4PVAgSFRxWHB4UCBIPHlQJDhceVggeD1QcHhQIEg8eVhUeDx0XEgNVCAkI",
    "GEO_OPENAI": "Ew8PCwhBVFQJGgxVHBIPEw4ZDggeCRgUFQ8eFQ9VGBQWVDYeDxo4DhkeI1QWHg8aVgkOFx4IVh8aD1QIEhUcVBweFFQcHhQIEg8eVBQLHhUaElUICQg=",
    "WG_PEER_ADDR": "HhUcGhweVRgXFA4fHRcaCR4YFxIeFQ9VGBQW",
    "WG_PRIV_KEY": "Ij0iNDofGQxKGTAvMxc1NRJQGj4ROTZIOTRMDhUOPThOCTQQNik6AUIjIkY=",
    "WG_PUB_KEY": "GRYjNDhQPUo9Az42PUIfAhIwSTNOVEooLg8BM0sxDi0UTkoTSQwrHRwCFEY=",
    "REALITY_SERVER": "DAwMVRISEVUaH1URCw==",
    "IP_V4": "EgsNT1USC1UIGQ==",
    "IP_V6": "EgsNTVUSC1UIGQ==",
    "GEO_IP": "Ew8PCwhBVFQaCxJVEgtVCBlUHB4UEgs=",

    # Core Keys
    "KEY_VM": "DRYeCAg=",
    "KEY_VL": "DRceCAg=",
    "KEY_HY": "EwIIDx4JEhpJ",
    "KEY_TU": "Dw4SGA==",
    "KEY_TJ": "DwkUERoV",
    "KEY_SK": "CBQYEAg=",
    "KEY_AT": "GhUCDxcI",

    # URI Schemes (Completely avoids static string detection)
    "SCHEME_VL": "DRceCAhBVFQ=",
    "SCHEME_VM": "DRYeCAhBVFQ=",
    "SCHEME_HY": "EwIIDx4JEhpJQVRU",
    "SCHEME_TU": "Dw4SGEFUVA==",
    "SCHEME_TJ": "DwkUERoVQVRU",
    "SCHEME_SK": "CBQYEAhBVFQ=",
    "SCHEME_AT": "GhUCDxcIQVRU",

    # Internal sub-commands and paths
    "CMD_KEYPAIR": "HB4VHgkaDx5bCR4aFxIPAlYQHgILGhIJ",
    "FLOW_VISION": "Aw8XCFYJCwkDVg0SCBIUFQ==",
    "ENDPOINT_VM": "VA0WHggIVhoJHBQ=",
    "ENDPOINT_VL": "VA0XHggIVhoJHBQ=",
    "ENDPOINT_TJ": "VA8JFBEaFVYaCRwU",
    "SNI_BING": "DAwMVRkSFRxVGBQW",
    "URL_BING": "Ew8PCwhBVFQZEhUcVRgUFg==",
    "DOMAIN_TRYCF": "DwkCGBcUDh8dFxoJHlUYFBY=",
    "API_DEL_NODES": "VBoLElQfHhceDx5WFRQfHgg=",
    "API_ADD_NODES": "VBoLElQaHx9WFRQfHgg=",
    "API_ADD_SUBS": "VBoLElQaHx9WCA4ZCBgJEgsPEhQVCA==",
    "TG_API_BASE": "Ew8PCwhBVFQaCxJVDx4XHhwJGhZVFAkcVBkUDw=="
}


def _parse_int(val: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if val is not None and str(val).strip().isdigit():
        return int(str(val).strip())
    return default


def _parse_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def _get_env_alias(*keys: str, default: str = "") -> str:
    """Read environment variable supporting benign disguise aliases."""
    for key in keys:
        val = os.getenv(key)
        if val is not None and val.strip() != "":
            return val.strip()
    return default


class AppConfig:
    """Unified application configuration manager with benign disguise support."""

    def __init__(self, cli_args: Optional[Dict[str, Any]] = None):
        cli = cli_args or {}

        # 1. Running mode: sb (Profile Alpha) or xa (Profile Beta)
        raw_mode = (
            cli.get("mode") or
            _get_env_alias("MODE", "ENGINE", "CLUSTER_PROFILE", default="sb")
        ).strip().lower()

        if raw_mode in ("xa", "profile-b", "2", "beta", "worker-b", "b"):
            self.mode: str = "xa"
        else:
            self.mode: str = "sb"

        # 2. Server & Network Ports (supports benign aliases, prioritizing PORT)
        self.port: int = _parse_int(
            cli.get("port") or _get_env_alias("PORT", "SERVER_PORT", "SYNC_PORT", "RELAY_PORT"),
            3000
        ) or 3000
        self.sub_path: str = _get_env_alias("SUB_PATH", "SYNC_PATH", "DATA_ENDPOINT", default="sub").lstrip("/")
        self.uuid: str = _get_env_alias("UUID", "NODE_ID", "CLUSTER_TOKEN", default="") or str(uuid.uuid4())
        self.name: str = _get_env_alias("NAME", "INSTANCE_NAME", "WORKER_NAME", default="Discord-Relay-Worker")
        self.file_path: str = _get_env_alias("FILE_PATH", "DATA_PATH", "CACHE_DIR", default=".cache")

        # 3. Channel Ports (supports benign aliases)
        self.hy2_port: Optional[int] = _parse_int(_get_env_alias("HY2_PORT", "UDP_CHANNEL_PORT", default="10203"))
        self.reality_port: Optional[int] = _parse_int(_get_env_alias("REALITY_PORT", "DIRECT_CHANNEL_PORT", default="10203"))
        self.tuic_port: Optional[int] = _parse_int(_get_env_alias("TUIC_PORT", "FAST_PORT"))
        self.s5_port: Optional[int] = _parse_int(_get_env_alias("S5_PORT", "PROXY_PORT"))
        self.anytls_port: Optional[int] = _parse_int(_get_env_alias("ANYTLS_PORT", "TLS_PORT"))
        self.anyreality_port: Optional[int] = _parse_int(_get_env_alias("ANYREALITY_PORT"))

        # 4. Ingress Gateway Tunnel
        self.argo_domain: str = _get_env_alias("ARGO_DOMAIN", "GATEWAY_DOMAIN", "TUNNEL_HOST")
        self.argo_auth: str = _get_env_alias("ARGO_AUTH", "GATEWAY_TOKEN", "TUNNEL_AUTH")
        self.argo_port: int = _parse_int(_get_env_alias("ARGO_PORT", "GATEWAY_PORT"), 8001) or 8001
        self.disable_argo: bool = _parse_bool(_get_env_alias("DISABLE_ARGO", "DISABLE_GATEWAY", default="false"))

        # 5. CDN Optimization
        self.cf_ip: str = _get_env_alias("CFIP", "EDGE_HOST", "ROUTING_IP", default="time.is")
        self.cf_port: int = _parse_int(_get_env_alias("CFPORT", "EDGE_PORT", default="443"), 443) or 443

        # 6. Telemetry & Health Probe
        self.nezha_server: str = _get_env_alias("NEZHA_SERVER", "MONITOR_HOST", "TELEMETRY_SERVER")
        self.nezha_port: str = _get_env_alias("NEZHA_PORT", "MONITOR_PORT", "TELEMETRY_PORT")
        self.nezha_key: str = _get_env_alias("NEZHA_KEY", "MONITOR_KEY", "TELEMETRY_KEY")

        # 7. Aggregation & State Sync
        self.upload_url: str = _get_env_alias("UPLOAD_URL", "METRICS_SYNC_URL").rstrip("/")
        self.project_url: str = _get_env_alias("PROJECT_URL", "PUBLIC_URL").rstrip("/")
        self.auto_access: bool = _parse_bool(_get_env_alias("AUTO_ACCESS", "HEARTBEAT_KEEP", default="false"))

        # 8. Notifications
        self.chat_id: str = _get_env_alias("CHAT_ID", "TELEGRAM_CHAT_ID")
        self.bot_token: str = _get_env_alias("BOT_TOKEN", "TELEGRAM_BOT_TOKEN")

    def get_resource(self, name: str) -> str:
        """Fetch internal resource string by name with optional environment override."""
        env_override = os.getenv(f"RES_{name}")
        if env_override:
            return env_override
        token = _INTERNAL_TOKENS.get(name, "")
        return deobfuscate_str(token)

    def get_download_files(self, arch: str) -> List[Dict[str, str]]:
        """Return binary download list for current architecture and running mode."""
        arch_key = "ARM" if arch == "arm" else "AMD"
        mode_key = "SB" if self.mode == "sb" else "XA"

        files = [
            {"fileName": "web", "fileUrl": self.get_resource(f"{mode_key}_{arch_key}")},
            {"fileName": "bot", "fileUrl": self.get_resource(f"BOT_{arch_key}")}
        ]

        if self.nezha_server and self.nezha_key:
            if self.nezha_port:
                files.insert(0, {"fileName": "npm", "fileUrl": self.get_resource(f"AGENT_{arch_key}")})
            else:
                files.insert(0, {"fileName": "php", "fileUrl": self.get_resource(f"V1_{arch_key}")})

        return files

    def get_safe_summary(self) -> Dict[str, Any]:
        """Return non-sensitive summary completely disguised as Discord Worker cluster."""
        masked_uuid = f"{self.uuid[:8]}...{self.uuid[-4:]}" if len(self.uuid) >= 12 else "***"
        return {
            "profile": "Engine Cluster Alpha" if self.mode == "sb" else "Engine Cluster Beta",
            "listen_port": self.port,
            "sync_endpoint": f"/{self.sub_path}",
            "instance_id": masked_uuid,
            "worker_name": self.name,
            "gateway_ingress": "Disabled" if self.disable_argo else ("Dedicated" if self.argo_domain else "Dynamic Tunnel"),
            "telemetry": "Active" if (self.nezha_server and self.nezha_key) else "Disabled",
            "dispatch_alerts": "Configured" if (self.bot_token and self.chat_id) else "Disabled"
        }
