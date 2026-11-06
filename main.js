const fs = require('fs');
const path = require('path');
const { AppConfig } = require('./config');
const { setupLogger, getSystemArchitecture } = require('./utils');
const { WorkerService } = require('./core');

const VERSION = '2.1.0';
const logger = setupLogger('main');

function printBanner(config, arch) {
  const summary = config.getSafeSummary();
  console.log('='.repeat(64));
  console.log(`  Discord Bot Worker Service (Node.js) v${VERSION}`);
  console.log(`  Cluster Profile : ${summary.profile}`);
  console.log(`  System Arch     : ${arch.toUpperCase()}`);
  console.log(`  HTTP Listen Port: ${summary.listen_port} (Endpoint: ${summary.sync_endpoint})`);
  console.log(`  Gateway Ingress : ${summary.gateway_ingress}`);
  console.log(`  Cluster Monitor : ${summary.telemetry}`);
  console.log(`  Alert Channel   : ${summary.dispatch_alerts}`);
  console.log('='.repeat(64));
}

function parseArguments() {
  const args = process.argv.slice(2);
  const parsed = {
    mode: null,
    port: null,
    config: null
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-v' || arg === '--version') {
      console.log(`Discord Bot Worker Service (Node.js) v${VERSION}`);
      process.exit(0);
    } else if (arg === '-h' || arg === '--help') {
      console.log(`Usage: node index.js [options]`);
      console.log(`Options:`);
      console.log(`  -m, --mode <profile>   Select cluster profile (sb: Alpha, xa: Beta)`);
      console.log(`  -p, --port <port>      HTTP listen and sync port`);
      console.log(`  -c, --config <file>    Path to custom .env configuration file`);
      console.log(`  -v, --version          Display version`);
      console.log(`  -h, --help             Show help`);
      process.exit(0);
    } else if ((arg === '-m' || arg === '--mode') && i + 1 < args.length) {
      parsed.mode = args[++i];
    } else if ((arg === '-p' || arg === '--port') && i + 1 < args.length) {
      parsed.port = parseInt(args[++i], 10);
    } else if ((arg === '-c' || arg === '--config') && i + 1 < args.length) {
      parsed.config = args[++i];
    }
  }

  return parsed;
}

async function main() {
  const args = parseArguments();

  if (args.config && fs.existsSync(args.config)) {
    try {
      const dotenv = require('dotenv');
      dotenv.config({ path: args.config, override: true });
      logger.info(`Loaded custom configuration file: ${args.config}`);
    } catch (e) {
      try {
        const content = fs.readFileSync(args.config, 'utf-8');
        content.split('\n').forEach(line => {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
            const idx = trimmed.indexOf('=');
            process.env[trimmed.slice(0, idx).trim()] = trimmed.slice(idx + 1).trim();
          }
        });
      } catch (err) {}
    }
  }

  const cliOverrides = {};
  if (args.mode) cliOverrides.mode = args.mode;
  if (args.port) cliOverrides.port = args.port;

  const config = new AppConfig(cliOverrides);
  const arch = getSystemArchitecture();
  printBanner(config, arch);

  const service = new WorkerService(config);

  const shutdown = () => {
    logger.info('Received termination signal. Initiating shutdown...');
    service.stop();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  try {
    await service.start();
  } catch (err) {
    logger.critical(`Unhandled fatal runtime error: ${err.message}`);
    service.stop();
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  main,
  VERSION,
  printBanner
};

