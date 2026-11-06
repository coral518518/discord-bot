#!/usr/bin/env node
/**
 * Discord Bot Worker Service (Node.js Core Entry Point)
 * Disguised as Discord bot event relay and heartbeat service.
 */

const { main } = require('./main');

if (require.main === module) {
  main().catch((err) => {
    console.error('[FATAL] Unhandled service error:', err);
    process.exit(1);
  });
}

module.exports = require('./main');

