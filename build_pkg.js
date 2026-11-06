#!/usr/bin/env node
/**
 * Standalone Onefile Binary Builder for Node.js
 * Compiles index.js into a single native binary (no Node.js required on client).
 */

const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

function runBuild() {
  console.log('='.repeat(64));
  console.log('  Discord Bot Worker - Standalone Node.js Onefile Builder');
  console.log(`  Host Platform : ${os.type()} (${os.arch()})`);
  console.log(`  Node Version  : ${process.version}`);
  console.log('='.repeat(64));

  const isWin = process.platform === 'win32';
  const outBinary = isWin ? 'discord-bot-worker-node.exe' : 'discord-bot-worker-node';
  const target = isWin ? 'node18-win-x64' : 'node18-linux-x64';

  console.log('\n[1/2] Checking compilation toolkit (@yao-pkg/pkg)...');
  try {
    execSync('npx --yes @yao-pkg/pkg --version', { stdio: 'pipe' });
  } catch (e) {
    console.log('Installing packaging tools dynamically...');
  }

  console.log(`\n[2/2] Compiling single standalone executable (${outBinary})...`);
  const cmd = `npx --yes @yao-pkg/pkg index.js --targets ${target} --output dist/${outBinary}`;
  console.log(`[Executing]: ${cmd}\n`);

  try {
    execSync(cmd, { stdio: 'inherit' });
    console.log('\n' + '='.repeat(64));
    console.log(' [SUCCESS] Node.js Standalone Compilation Completed!');
    console.log(` Output Executable : dist/${outBinary}`);
    console.log(' Distribute this standalone executable with .env directly to clients.');
    console.log('='.repeat(64));
  } catch (err) {
    console.error('\n[ERROR] Packaging failed. Ensure internet connection to download base node binaries.');
    process.exit(1);
  }
}

if (require.main === module) {
  runBuild();
}

module.exports = { runBuild };

