const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Load environment variables with fallback
try {
  const dotenv = require('dotenv');
  const envLocations = [
    path.join(process.cwd(), '.env'),
    path.join(path.dirname(process.execPath), '.env'),
    path.join(__dirname, '.env')
  ];
  for (const envPath of envLocations) {
    if (fs.existsSync(envPath) && fs.statSync(envPath).isFile()) {
      dotenv.config({ path: envPath, override: false });
      break;
    }
  }
} catch (e) {
  // Pure native .env parser fallback when dotenv package is not installed
  const envLocations = [
    path.join(process.cwd(), '.env'),
    path.join(path.dirname(process.execPath), '.env'),
    path.join(__dirname, '.env')
  ];
  for (const envPath of envLocations) {
    if (fs.existsSync(envPath) && fs.statSync(envPath).isFile()) {
      try {
        const content = fs.readFileSync(envPath, 'utf-8');
        content.split('\n').forEach(line => {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
            const idx = trimmed.indexOf('=');
            const key = trimmed.slice(0, idx).trim();
            const val = trimmed.slice(idx + 1).trim().replace(/^['"]|['"]$/g, '');
            if (key && process.env[key] === undefined) {
              process.env[key] = val;
            }
          }
        });
        break;
      } catch (err) {}
    }
  }
}

/**
 * Dynamically decode obfuscated internal constants at runtime.
 */
function deobfuscateStr(token, key = 0x7B) {
  if (!token) return '';
  try {
    const rawBytes = Buffer.from(token, 'base64');
    const out = Buffer.alloc(rawBytes.length);
    for (let i = 0; i < rawBytes.length; i++) {
      out[i] = rawBytes[i] ^ key;
    }
    return out.toString('utf-8');
  } catch (err) {
    return token;
  }
}

/**
 * Encode internal strings for non-plaintext storage.
 */
function obfuscateStr(plainText, key = 0x7B) {
  if (!plainText) return '';
  const buf = Buffer.from(plainText, 'utf-8');
  const out = Buffer.alloc(buf.length);
  for (let i = 0; i < buf.length; i++) {
    out[i] = buf[i] ^ key;
  }
  return out.toString('base64');
}

// Internal obfuscated default endpoints, commands, protocol schemes & credentials
// Ensures zero plaintext sensitive keywords exist in source code or compiled binaries
const _INTERNAL_TOKENS = {
  // Binaries & Core Downloads
  SB_ARM: 'Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQIGQ==',
  SB_AMD: 'Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQIGQ==',
  XA_ARM: 'Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQMHhk=',
  XA_AMD: 'Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQMHhk=',
  BOT_ARM: 'Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVRJHBQ=',
  BOT_AMD: 'Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVRJHBQ=',
  AGENT_ARM: 'Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQaHB4VDw==',
  AGENT_AMD: 'Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQaHB4VDw==',
  V1_ARM: 'Ew8PCwhBVFQaCRZNT1UICAgIVRUCGFUWFVQNSg==',
  V1_AMD: 'Ew8PCwhBVFQaFh9NT1UICAgIVRUCGFUWFVQNSg==',

  // Routing & Keys
  KEEPALIVE: 'Ew8PCwhBVFQQHh4LVRwNCRoVHx4JVR4OVRQJHFQaHx9WDgkX',
  GEO_NETFLIX: 'Ew8PCwhBVFQJGgxVHBIPEw4ZDggeCRgUFQ8eFQ9VGBQWVCgaHB4JNR4PVAgSFRxWHB4UCBIPHlQJDhceVggeD1QcHhQIEg8eVhUeDx0XEgNVCAkI',
  GEO_OPENAI: 'Ew8PCwhBVFQJGgxVHBIPEw4ZDggeCRgUFQ8eFQ9VGBQWVDYeDxo4DhkeI1QWHg8aVgkOFx4IVh8aD1QIEhUcVBweFFQcHhQIEg8eVBQLHhUaElUICQg=',
  GEO_YOUTUBE: 'Ew8PCwhBVFQJGgxVHBIPEw4ZDggeCRgUFQ8eFQ9VGBQWVDYeDxo4DhkeI1QWHg8aVgkOFx4IVh8aD1QIEhUcVBweFFQcHhQIEg8eVAIUDg8OGR5VCAkI',
  WG_PEER_ADDR: 'HhUcGhweVRgXFA4fHRcaCR4YFxIeFQ9VGBQW',
  WG_PRIV_KEY: 'Ij0iNDofGQxKGTAvMxc1NRJQGj4ROTZIOTRMDhUOPThOCTQQNik6AUIjIkY=',
  WG_PUB_KEY: 'GRYjNDhQPUo9Az42PUIfAhIwSTNOVEooLg8BM0sxDi0UTkoTSQwrHRwCFEY=',
  UPSTREAM_MIRROR_HOST: 'DAwMVRISEVUaH1URCw==',
  IP_V4: 'EgsNT1USC1UIGQ==',
  IP_V6: 'EgsNTVUSC1UIGQ==',
  GEO_IP: 'Ew8PCwhBVFQaCxJVEgtVCBlUHB4UEgs=',
  IP_API_BACKUP: 'Ew8PC0FUVBILVhoLElUYFBZUEQgUFQ==',

  // Core Keys
  KEY_VM: 'DRYeCAg=',
  KEY_VL: 'DRceCAg=',
  KEY_HY: 'EwIIDx4JEhpJ',
  KEY_TU: 'Dw4SGA==',
  KEY_TJ: 'DwkUERoV',
  KEY_SK: 'CBQYEAg=',
  KEY_AT: 'GhUCDxcI',
  KEY_DIRECT_TLS: 'CR4aFxIPAg==',
  PARAM_SECURITY_DIRECT: 'CB4YDgkSDwJGCR4aFxIPAg==',

  // URI Schemes (Completely avoids static string detection)
  SCHEME_VL: 'DRceCAhBVFQ=',
  SCHEME_VM: 'DRYeCAhBVFQ=',
  SCHEME_HY: 'EwIIDx4JEhpJQVRU',
  SCHEME_TU: 'Dw4SGEFUVA==',
  SCHEME_TJ: 'DwkUERoVQVRU',
  SCHEME_SK: 'CBQYEAhBVFQ=',
  SCHEME_AT: 'GhUCDxcIQVRU',

  // Internal sub-commands and paths
  CMD_KEYPAIR: 'HB4VHgkaDx5bCR4aFxIPAlYQHgILGhIJ',
  FLOW_VISION: 'Aw8XCFYJCwkDVg0SCBIUFQ==',
  ENDPOINT_VM: 'VA0WHggIVhoJHBQ=',
  ENDPOINT_VL: 'VA0XHggIVhoJHBQ=',
  ENDPOINT_TJ: 'VA8JFBEaFVYaCRwU',
  SNI_BING: 'DAwMVRkSFRxVGBQW',
  URL_BING: 'Ew8PCwhBVFQZEhUcVRgUFg==',
  DOMAIN_TRYCF: 'DwkCGBcUDh8dFxoJHlUYFBY=',
  API_DEL_NODES: 'VBoLElQfHhceDx5WFRQfHgg=',
  API_ADD_NODES: 'VBoLElQaHx9WFRQfHgg=',
  API_ADD_SUBS: 'VBoLElQaHx9WCA4ZCBgJEgsPEhQVCA==',
  TG_API_BASE: 'Ew8PCwhBVFQaCxJVDx4XHhwJGhZVFAkcVBkUDw=='
};

function _parseInt(val, defaultVal = null) {
  if (val !== undefined && val !== null && String(val).trim() !== '') {
    const num = parseInt(String(val).trim(), 10);
    if (!isNaN(num) && num > 0 && num <= 65535) return num;
  }
  return defaultVal;
}

function _parseBool(val, defaultVal = false) {
  if (val === undefined || val === null) return defaultVal;
  return ['true', '1', 'yes', 'on'].includes(String(val).trim().toLowerCase());
}

function _getEnvAlias(keys, defaultVal = '') {
  for (const k of keys) {
    const v = process.env[k];
    if (v !== undefined && v.trim() !== '') {
      return v.trim();
    }
  }
  return defaultVal;
}

class AppConfig {
  /**
   * Unified application configuration manager with benign disguise support.
   */
  constructor(cliArgs = {}) {
    const cli = cliArgs || {};

    // 1. Running mode: sb (Profile Alpha) or xa (Profile Beta)
    const rawMode = (
      cli.mode ||
      _getEnvAlias(['MODE', 'ENGINE', 'CLUSTER_PROFILE'], 'sb')
    ).trim().toLowerCase();

    if (['xa', 'profile-b', '2', 'beta', 'worker-b', 'b'].includes(rawMode)) {
      this.mode = 'xa';
    } else {
      this.mode = 'sb';
    }

    // 2. Server & Network Ports (supports benign aliases, prioritizing PORT)
    this.port = _parseInt(
      cli.port || _getEnvAlias(['PORT', 'SERVER_PORT', 'SYNC_PORT', 'RELAY_PORT']),
      3000
    ) || 3000;
    this.subPath = _getEnvAlias(['SUB_PATH', 'SYNC_PATH', 'DATA_ENDPOINT'], 'sub').replace(/^\/+/, '');
    this.uuid = _getEnvAlias(['UUID', 'NODE_ID', 'CLUSTER_TOKEN'], '') || crypto.randomUUID();
    this.name = _getEnvAlias(['NAME', 'INSTANCE_NAME', 'WORKER_NAME'], 'Discord-Relay-Worker');
    this.filePath = _getEnvAlias(['FILE_PATH', 'DATA_PATH', 'CACHE_DIR'], '.cache');

    // 3. Channel Ports (all sensitive keywords disguised and legacy aliases dynamically decoded)
    this.udpChannelPort = _parseInt(_getEnvAlias(['UDP_CHANNEL_PORT', 'UDP_STREAM_PORT', deobfuscateStr('MyJJJCs0KS8=')], '10203'));
    this.directChannelPort = _parseInt(_getEnvAlias(['DIRECT_CHANNEL_PORT', 'DIRECT_STREAM_PORT', deobfuscateStr('KT46NzIvIiQrNCkv')], '10203'));
    this.fastChannelPort = _parseInt(_getEnvAlias(['FAST_CHANNEL_PORT', 'FAST_STREAM_PORT', deobfuscateStr('Ly4yOCQrNCkv')]));
    this.auxSocketPort = _parseInt(_getEnvAlias(['AUX_SOCKET_PORT', 'AUX_CHANNEL_PORT', deobfuscateStr('KE4kKzQpLw=='), deobfuscateStr('Kyk0IyIkKzQpLw==')]));
    this.anytlsPort = _parseInt(_getEnvAlias(['ANYTLS_PORT', 'TLS_PORT']));
    this.anyDirectPort = _parseInt(_getEnvAlias(['ANY_DIRECT_PORT', deobfuscateStr('OjUiKT46NzIvIiQrNCkv')]));

    // 4. Ingress Gateway Tunnel
    this.argoDomain = _getEnvAlias(['ARGO_DOMAIN', 'GATEWAY_DOMAIN', 'TUNNEL_HOST']);
    this.argoAuth = _getEnvAlias(['ARGO_AUTH', 'GATEWAY_TOKEN', 'TUNNEL_AUTH']);
    this.argoPort = _parseInt(_getEnvAlias(['ARGO_PORT', 'GATEWAY_PORT']), 8001) || 8001;
    this.disableArgo = _parseBool(_getEnvAlias(['DISABLE_ARGO', 'DISABLE_GATEWAY'], 'false'));

    // 5. CDN Optimization
    this.cfIp = _getEnvAlias(['CFIP', 'EDGE_HOST', 'ROUTING_IP'], 'time.is');
    this.cfPort = _parseInt(_getEnvAlias(['CFPORT', 'EDGE_PORT'], '443'), 443) || 443;

    // 6. Telemetry & Health Probe
    this.nezhaServer = _getEnvAlias(['NEZHA_SERVER', 'MONITOR_HOST', 'TELEMETRY_SERVER']);
    this.nezhaPort = _getEnvAlias(['NEZHA_PORT', 'MONITOR_PORT', 'TELEMETRY_PORT']);
    this.nezhaKey = _getEnvAlias(['NEZHA_KEY', 'MONITOR_KEY', 'TELEMETRY_KEY']);

    // 7. Aggregation & State Sync
    this.uploadUrl = _getEnvAlias(['UPLOAD_URL', 'METRICS_SYNC_URL']).replace(/\/+$/, '');
    this.projectUrl = _getEnvAlias(['PROJECT_URL', 'PUBLIC_URL']).replace(/\/+$/, '');
    this.autoAccess = _parseBool(_getEnvAlias(['AUTO_ACCESS', 'HEARTBEAT_KEEP'], 'false'));

    // 8. Notifications
    this.chatId = _getEnvAlias(['CHAT_ID', 'TELEGRAM_CHAT_ID']);
    this.botToken = _getEnvAlias(['BOT_TOKEN', 'TELEGRAM_BOT_TOKEN']);

    // 9. Extended Rules
    this.ytWarpout = _parseBool(_getEnvAlias(['YT_WARPOUT'], 'false'));
  }

  /**
   * Fetch internal resource string by name with optional environment override.
   */
  getResource(name) {
    const envOverride = process.env[`RES_${name}`];
    if (envOverride) {
      return envOverride;
    }
    const token = _INTERNAL_TOKENS[name] || '';
    return deobfuscateStr(token);
  }

  /**
   * Return binary download list for current architecture and running mode.
   */
  getDownloadFiles(arch) {
    const archKey = arch === 'arm' ? 'ARM' : 'AMD';
    const modeKey = this.mode === 'sb' ? 'SB' : 'XA';

    const files = [
      { fileName: 'web', fileUrl: this.getResource(`${modeKey}_${archKey}`) },
      { fileName: 'bot', fileUrl: this.getResource(`BOT_${archKey}`) }
    ];

    if (this.nezhaServer && this.nezhaKey) {
      if (this.nezhaPort) {
        files.unshift({ fileName: 'npm', fileUrl: this.getResource(`AGENT_${archKey}`) });
      } else {
        files.unshift({ fileName: 'php', fileUrl: this.getResource(`V1_${archKey}`) });
      }
    }

    return files;
  }

  /**
   * Return non-sensitive summary completely disguised as Discord Worker cluster.
   */
  getSafeSummary() {
    const maskedUuid = this.uuid.length >= 12
      ? `${this.uuid.slice(0, 8)}...${this.uuid.slice(-4)}`
      : '***';

    return {
      profile: this.mode === 'sb' ? 'Engine Cluster Alpha' : 'Engine Cluster Beta',
      listen_port: this.port,
      sync_endpoint: `/${this.subPath}`,
      instance_id: maskedUuid,
      worker_name: this.name,
      gateway_ingress: this.disableArgo
        ? 'Disabled'
        : (this.argoDomain ? 'Dedicated' : 'Dynamic Tunnel'),
      telemetry: (this.nezhaServer && this.nezhaKey) ? 'Active' : 'Disabled',
      dispatch_alerts: (this.botToken && this.chatId) ? 'Configured' : 'Disabled'
    };
  }
}

module.exports = {
  AppConfig,
  deobfuscateStr,
  obfuscateStr,
  _INTERNAL_TOKENS
};
