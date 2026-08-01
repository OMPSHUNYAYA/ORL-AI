'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const ORL_AI = require('../demo/ORL_AI_Browser_Resolver_v5_0_0.js');

const ROOT = path.resolve(__dirname, '..');

function nodeSha256(bytes) {
  return crypto.createHash('sha256').update(Buffer.from(bytes)).digest('hex');
}

function deterministicBytes(length, seed) {
  let state = seed >>> 0;
  const bytes = new Uint8Array(length);
  for (let index = 0; index < length; index += 1) {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    bytes[index] = state & 0xff;
  }
  return bytes;
}

function isolatedResolver() {
  const source = fs.readFileSync(path.join(ROOT, 'demo', 'ORL_AI_Browser_Resolver_v5_0_0.js'), 'utf8');
  const sandbox = {
    console,
    TextEncoder,
    TextDecoder,
    Uint8Array,
    Uint32Array,
    DataView,
    ArrayBuffer,
    Set,
    Map,
    JSON,
    Math,
    Number,
    Object,
    String,
    Boolean,
    RegExp,
    Promise,
    window: {},
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: 'ORL_AI_Browser_Resolver_v5_0_0.js' });
  return sandbox.window.ORL_AI;
}

async function run() {
  const checks = [];
  const encoder = new TextEncoder();
  const vectors = [
    ['empty vector', new Uint8Array(), 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
    ['abc vector', encoder.encode('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
    ['long vector', encoder.encode('abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq'), '248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1'],
  ];
  for (const [name, bytes, expected] of vectors) {
    checks.push([name, ORL_AI.sha256HexPure(bytes) === expected]);
  }

  const boundaryLengths = [55, 56, 63, 64, 65];
  const boundariesPass = boundaryLengths.every(length => {
    const bytes = deterministicBytes(length, 0x51a25600 + length);
    return ORL_AI.sha256HexPure(bytes) === nodeSha256(bytes);
  });
  checks.push(['padding-boundary lengths', boundariesPass]);

  const unicodeBytes = encoder.encode('ORL-AI | \u03bb | \u0ba4\u0bae\u0bbf\u0bb4\u0bcd | \ud83d\ude80');
  checks.push(['Unicode bytes', ORL_AI.sha256HexPure(unicodeBytes) === nodeSha256(unicodeBytes)]);

  let fuzzPass = true;
  for (let index = 0; index < 500; index += 1) {
    const length = (index * 37) % 1025;
    const bytes = deterministicBytes(length, 0x9e3779b9 ^ index);
    if (ORL_AI.sha256HexPure(bytes) !== nodeSha256(bytes)) {
      fuzzPass = false;
      break;
    }
  }
  checks.push(['deterministic fuzz corpus 500/500', fuzzPass]);

  const nativeProbe = deterministicBytes(257, 0x0a11ce55);
  const nativeDigest = await ORL_AI.sha256Hex(nativeProbe, false);
  const forcedPureDigest = await ORL_AI.sha256Hex(nativeProbe, true);
  checks.push(['forced pure path equals native path', nativeDigest === forcedPureDigest]);

  const isolated = isolatedResolver();
  checks.push(['origin-independent backend selection', isolated.hashBackendName() === 'PURE_JAVASCRIPT_SHA256']);

  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'corpus', 'ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json'), 'utf8'));
  for (const entry of manifest.entries) {
    const input = JSON.parse(fs.readFileSync(path.join(ROOT, entry.input_path), 'utf8'));
    const expectedBundle = fs.readFileSync(path.join(ROOT, entry.bundle_path), 'utf8');
    const expectedReceipt = fs.readFileSync(path.join(ROOT, entry.receipt_path), 'utf8');
    const actual = await isolated.resolveDocument(input);
    const passed = isolated.canonicalText(actual.bundle) === expectedBundle && isolated.canonicalText(actual.receipt) === expectedReceipt;
    checks.push(['isolated fallback parity ' + entry.case_id, passed]);
  }

  let passed = 0;
  for (const [name, status] of checks) {
    if (status) passed += 1;
    console.log((status ? 'PASS' : 'FAIL') + '  ' + name);
  }
  console.log('TOTAL ' + passed + '/' + checks.length + ' PASS');
  console.log('SHA-256 FALLBACK VERIFY: ' + (passed === checks.length ? 'PASS' : 'FAIL'));
  return passed === checks.length ? 0 : 1;
}

run()
  .then(code => { process.exitCode = code; })
  .catch(error => {
    console.error(error.stack || String(error));
    process.exitCode = 1;
  });
