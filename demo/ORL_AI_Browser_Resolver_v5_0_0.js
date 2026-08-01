'use strict';

const ORL_AI = (() => {
  const PROJECT = 'ORL-AI';
  const VERSION = '5.0.0';
  const INPUT_SCHEMA = 'ORL-AI-INPUT-5.0.0';
  const BUNDLE_SCHEMA = 'ORL-AI-BUNDLE-5.0.0';
  const RECEIPT_SCHEMA = 'ORL-AI-PUBLIC-RECEIPT-5.0.0';
  const RULESET_ID = 'ORL-AI-ADMISSION-RULESET-5-D01';
  const PROFILE_ID = 'ORL-AI-STRICT-3CLASS-5-D01';
  const TEXT_PROFILE_ID = 'ORL-AI-UNICODE-SCALAR-EXACT-5-D01';
  const ARTIFACT_PROFILE_ID = 'ORL-AI-CANONICAL-SHA256-5-D01';
  const REQUIRED_CLASSES = new Set(['MODEL', 'MODEL_REVIEW', 'RULE_CHECK']);
  const VALID_CLASSES = new Set(['MODEL', 'MODEL_REVIEW', 'RULE_CHECK', 'HUMAN_REVIEW', 'TOOL_CHECK']);
  const ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
  const DIGEST_RE = /^sha256:[0-9a-f]{64}$/;
  const MAX_EXACT_INTEGER = 9007199254740991;
  const MAX_CANDIDATES = 32;
  const MAX_SOURCES = 128;
  const MAX_EVIDENCE = 256;
  const MAX_OBSERVATIONS = 256;
  const MAX_CONSTRAINTS = 128;
  const MAX_STRING_LENGTH = 512;
  const MAX_ARRAY_LENGTH = 512;
  const MAX_DEPTH = 16;

  function compareScalarSequence(left, right) {
    const first = Array.from(left, character => character.codePointAt(0));
    const second = Array.from(right, character => character.codePointAt(0));
    const length = Math.min(first.length, second.length);
    for (let index = 0; index < length; index += 1) {
      if (first[index] < second[index]) return -1;
      if (first[index] > second[index]) return 1;
    }
    return first.length < second.length ? -1 : (first.length > second.length ? 1 : 0);
  }

  const sortStrings = values => values.sort(compareScalarSequence);
  const uniqueSorted = values => sortStrings([...new Set(values)]);

  function textIssue(value) {
    if (Array.from(value).length > MAX_STRING_LENGTH) return 'STRING_TOO_LONG';
    for (const character of value) {
      const code = character.codePointAt(0);
      if (code >= 0xd800 && code <= 0xdfff) return 'SURROGATE_CODE_POINT';
      if (code === 0x0d) return 'CARRIAGE_RETURN';
      if (code === 0xfeff) return 'ZERO_WIDTH_NO_BREAK_SPACE';
      if (code < 0x20 && code !== 0x09 && code !== 0x0a) return 'CONTROL_CODE_POINT';
      if (code >= 0x7f && code <= 0x9f) return 'CONTROL_CODE_POINT';
    }
    return null;
  }

  function walkShape(value, path, depth, errors) {
    if (depth > MAX_DEPTH) {
      errors.push('RESOURCE_DEPTH_EXCEEDED:' + path);
      return;
    }
    if (value === null || typeof value === 'boolean') return;
    if (typeof value === 'number') {
      if (!Number.isFinite(value) || !Number.isInteger(value)) errors.push('FLOATING_NUMBER:' + path);
      else if (!Number.isSafeInteger(value) || value < -MAX_EXACT_INTEGER || value > MAX_EXACT_INTEGER) errors.push('INTEGER_OUTSIDE_EXACT_RANGE:' + path);
      return;
    }
    if (typeof value === 'string') {
      const issue = textIssue(value);
      if (issue) errors.push(issue + ':' + path);
      return;
    }
    if (Array.isArray(value)) {
      if (value.length > MAX_ARRAY_LENGTH) errors.push('RESOURCE_ARRAY_EXCEEDED:' + path);
      value.forEach((item, index) => walkShape(item, path + '[' + index + ']', depth + 1, errors));
      return;
    }
    if (value && typeof value === 'object') {
      const keys = Object.keys(value);
      if (keys.length > MAX_ARRAY_LENGTH) errors.push('RESOURCE_OBJECT_EXCEEDED:' + path);
      for (const key of keys) {
        const issue = textIssue(key);
        if (issue) errors.push(issue + ':' + path + '.<key>');
        walkShape(value[key], path + '.' + key, depth + 1, errors);
      }
      return;
    }
    errors.push('UNSUPPORTED_RUNTIME_TYPE:' + path);
  }

  function sortedObject(value) {
    if (Array.isArray(value)) return value.map(sortedObject);
    if (value && typeof value === 'object') {
      const out = Object.create(null);
      for (const key of Object.keys(value).sort(compareScalarSequence)) out[key] = sortedObject(value[key]);
      return out;
    }
    return value;
  }

  function canonicalText(value) {
    return JSON.stringify(sortedObject(value)) + '\n';
  }

  function sha256HexPure(bytes) {
    const constants = new Uint32Array([
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ]);
    const state = new Uint32Array([
      0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    ]);
    const length = bytes.length;
    const withMarker = length + 1;
    const totalLength = withMarker + (((56 - (withMarker % 64)) + 64) % 64) + 8;
    const buffer = new Uint8Array(totalLength);
    buffer.set(bytes, 0);
    buffer[length] = 0x80;
    const view = new DataView(buffer.buffer);
    view.setUint32(totalLength - 8, Math.floor(length / 0x20000000) >>> 0, false);
    view.setUint32(totalLength - 4, (length << 3) >>> 0, false);
    const words = new Uint32Array(64);
    const rotateRight = (value, count) => ((value >>> count) | (value << (32 - count))) >>> 0;

    for (let offset = 0; offset < totalLength; offset += 64) {
      for (let index = 0; index < 16; index += 1) {
        words[index] = view.getUint32(offset + index * 4, false);
      }
      for (let index = 16; index < 64; index += 1) {
        const sigma0 = rotateRight(words[index - 15], 7) ^ rotateRight(words[index - 15], 18) ^ (words[index - 15] >>> 3);
        const sigma1 = rotateRight(words[index - 2], 17) ^ rotateRight(words[index - 2], 19) ^ (words[index - 2] >>> 10);
        words[index] = (words[index - 16] + sigma0 + words[index - 7] + sigma1) >>> 0;
      }

      let [a, b, c, d, e, f, g, h] = state;
      for (let index = 0; index < 64; index += 1) {
        const sum1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
        const choose = (e & f) ^ (~e & g);
        const temporary1 = (h + sum1 + choose + constants[index] + words[index]) >>> 0;
        const sum0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
        const majority = (a & b) ^ (a & c) ^ (b & c);
        const temporary2 = (sum0 + majority) >>> 0;
        h = g;
        g = f;
        f = e;
        e = (d + temporary1) >>> 0;
        d = c;
        c = b;
        b = a;
        a = (temporary1 + temporary2) >>> 0;
      }

      state[0] = (state[0] + a) >>> 0;
      state[1] = (state[1] + b) >>> 0;
      state[2] = (state[2] + c) >>> 0;
      state[3] = (state[3] + d) >>> 0;
      state[4] = (state[4] + e) >>> 0;
      state[5] = (state[5] + f) >>> 0;
      state[6] = (state[6] + g) >>> 0;
      state[7] = (state[7] + h) >>> 0;
    }

    return Array.from(state, value => value.toString(16).padStart(8, '0')).join('');
  }

  function nativeHashBackend() {
    if (typeof globalThis.crypto !== 'undefined' && globalThis.crypto.subtle) {
      return { name: 'WEB_CRYPTO', subtle: globalThis.crypto.subtle };
    }
    if (typeof require === 'function') {
      try {
        const webcrypto = require('crypto').webcrypto;
        if (webcrypto && webcrypto.subtle) return { name: 'NODE_WEB_CRYPTO', subtle: webcrypto.subtle };
      } catch (error) {
        return null;
      }
    }
    return null;
  }

  function hashBackendName() {
    const backend = nativeHashBackend();
    return backend ? backend.name : 'PURE_JAVASCRIPT_SHA256';
  }

  async function sha256Hex(bytes, forcePure) {
    const backend = forcePure ? null : nativeHashBackend();
    if (backend) {
      const digest = await backend.subtle.digest('SHA-256', bytes);
      return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    }
    return sha256HexPure(bytes);
  }

  async function taggedHash(tag, value) {
    const encoder = new TextEncoder();
    const prefix = encoder.encode(tag + '\u0000');
    const body = encoder.encode(canonicalText(value));
    const bytes = new Uint8Array(prefix.length + body.length);
    bytes.set(prefix, 0);
    bytes.set(body, prefix.length);
    return 'sha256:' + await sha256Hex(bytes);
  }

  function exactFields(value, required, path, errors) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      errors.push('EXPECTED_OBJECT:' + path);
      return false;
    }
    const wanted = new Set(required);
    const actual = new Set(Object.keys(value));
    for (const key of [...wanted].filter(key => !actual.has(key)).sort(compareScalarSequence)) errors.push('MISSING_FIELD:' + path + '.' + key);
    for (const key of [...actual].filter(key => !wanted.has(key)).sort(compareScalarSequence)) errors.push('UNSUPPORTED_FIELD:' + path + '.' + key);
    return true;
  }

  function uniqueStrings(value, path, errors) {
    if (!Array.isArray(value)) {
      errors.push('EXPECTED_ARRAY:' + path);
      return [];
    }
    const seen = new Set();
    const out = [];
    value.forEach((item, index) => {
      if (typeof item !== 'string' || !ID_RE.test(item)) errors.push('INVALID_IDENTIFIER:' + path + '[' + index + ']');
      if (seen.has(item)) errors.push('DUPLICATE_ARRAY_VALUE:' + path + '[' + index + ']');
      seen.add(item);
      out.push(item);
    });
    return out;
  }

  function normalize(document) {
    const errors = [];
    walkShape(document, '$', 0, errors);
    if (!exactFields(document, ['schema', 'context', 'sources', 'evidence', 'observations', 'constraints', 'boundary'], '$', errors)) return [null, uniqueSorted(errors)];
    if (document.schema !== INPUT_SCHEMA) errors.push('UNSUPPORTED_SCHEMA:$.schema');
    const context = document.context;
    const contextFields = ['context_id', 'question_id', 'domain', 'candidate_ids', 'ruleset_id', 'profile_id', 'text_profile_id', 'evidence_mode', 'authority_mode', 'boundary_state'];
    if (!exactFields(context, contextFields, '$.context', errors)) return [null, uniqueSorted(errors)];
    for (const field of ['context_id', 'question_id', 'domain']) if (typeof context[field] !== 'string' || !ID_RE.test(context[field])) errors.push('INVALID_IDENTIFIER:$.context.' + field);
    const candidates = uniqueStrings(context.candidate_ids, '$.context.candidate_ids', errors);
    if (candidates.length === 0) errors.push('EMPTY_CANDIDATE_SET:$.context.candidate_ids');
    if (candidates.length > MAX_CANDIDATES) errors.push('RESOURCE_CANDIDATE_LIMIT:$.context.candidate_ids');
    if (context.ruleset_id !== RULESET_ID) errors.push('UNSUPPORTED_RULESET:$.context.ruleset_id');
    if (context.profile_id !== PROFILE_ID) errors.push('UNSUPPORTED_PROFILE:$.context.profile_id');
    if (context.text_profile_id !== TEXT_PROFILE_ID) errors.push('UNSUPPORTED_TEXT_PROFILE:$.context.text_profile_id');
    if (context.evidence_mode !== 'DECLARED') errors.push('UNSUPPORTED_EVIDENCE_MODE:$.context.evidence_mode');
    if (context.authority_mode !== 'NONE') errors.push('CALLER_DERIVED_AUTHORITY_FORBIDDEN:$.context.authority_mode');
    if (!new Set(['OPEN', 'SEALED']).has(context.boundary_state)) errors.push('UNSUPPORTED_BOUNDARY_STATE:$.context.boundary_state');

    const sources = new Map();
    if (!Array.isArray(document.sources)) errors.push('EXPECTED_ARRAY:$.sources');
    else {
      if (document.sources.length > MAX_SOURCES) errors.push('RESOURCE_SOURCE_LIMIT:$.sources');
      document.sources.forEach((item, index) => {
      const path = '$.sources[' + index + ']';
      if (!exactFields(item, ['source_id', 'source_family', 'source_class'], path, errors)) return;
      if (typeof item.source_id !== 'string' || !ID_RE.test(item.source_id)) errors.push('INVALID_IDENTIFIER:' + path + '.source_id');
      if (sources.has(item.source_id)) errors.push('DUPLICATE_SOURCE_ID:' + path + '.source_id');
      if (typeof item.source_family !== 'string' || !ID_RE.test(item.source_family)) errors.push('INVALID_IDENTIFIER:' + path + '.source_family');
      if (!VALID_CLASSES.has(item.source_class)) errors.push('UNSUPPORTED_SOURCE_CLASS:' + path + '.source_class');
      sources.set(item.source_id, {...item});
      });
    }

    const evidence = new Map();
    if (!Array.isArray(document.evidence)) errors.push('EXPECTED_ARRAY:$.evidence');
    else {
      if (document.evidence.length > MAX_EVIDENCE) errors.push('RESOURCE_EVIDENCE_LIMIT:$.evidence');
      document.evidence.forEach((item, index) => {
      const path = '$.evidence[' + index + ']';
      if (!exactFields(item, ['evidence_id', 'kind', 'digest'], path, errors)) return;
      if (typeof item.evidence_id !== 'string' || !ID_RE.test(item.evidence_id)) errors.push('INVALID_IDENTIFIER:' + path + '.evidence_id');
      if (evidence.has(item.evidence_id)) errors.push('DUPLICATE_EVIDENCE_ID:' + path + '.evidence_id');
      if (typeof item.kind !== 'string' || !ID_RE.test(item.kind)) errors.push('INVALID_IDENTIFIER:' + path + '.kind');
      if (typeof item.digest !== 'string' || !DIGEST_RE.test(item.digest)) errors.push('INVALID_EVIDENCE_DIGEST:' + path + '.digest');
      evidence.set(item.evidence_id, {...item});
      });
    }

    const observations = new Map();
    if (!Array.isArray(document.observations)) errors.push('EXPECTED_ARRAY:$.observations');
    else {
      if (document.observations.length > MAX_OBSERVATIONS) errors.push('RESOURCE_OBSERVATION_LIMIT:$.observations');
      document.observations.forEach((item, index) => {
      const path = '$.observations[' + index + ']';
      if (!exactFields(item, ['observation_id', 'source_id', 'candidate_id', 'stance', 'evidence_ids'], path, errors)) return;
      if (typeof item.observation_id !== 'string' || !ID_RE.test(item.observation_id)) errors.push('INVALID_IDENTIFIER:' + path + '.observation_id');
      if (observations.has(item.observation_id)) errors.push('DUPLICATE_OBSERVATION_ID:' + path + '.observation_id');
      if (!sources.has(item.source_id)) errors.push('UNKNOWN_SOURCE_REFERENCE:' + path + '.source_id');
      if (!new Set(candidates).has(item.candidate_id)) errors.push('UNKNOWN_CANDIDATE_REFERENCE:' + path + '.candidate_id');
      if (!new Set(['SUPPORT', 'OPPOSE', 'ABSTAIN']).has(item.stance)) errors.push('UNSUPPORTED_STANCE:' + path + '.stance');
      const refs = uniqueStrings(item.evidence_ids, path + '.evidence_ids', errors);
      if (refs.some(ref => !evidence.has(ref))) errors.push('UNKNOWN_EVIDENCE_REFERENCE:' + path + '.evidence_ids');
      observations.set(item.observation_id, {observation_id:item.observation_id, source_id:item.source_id, candidate_id:item.candidate_id, stance:item.stance, evidence_ids:[...refs].sort(compareScalarSequence)});
      });
    }

    const constraints = new Map();
    if (!Array.isArray(document.constraints)) errors.push('EXPECTED_ARRAY:$.constraints');
    else {
      if (document.constraints.length > MAX_CONSTRAINTS) errors.push('RESOURCE_CONSTRAINT_LIMIT:$.constraints');
      document.constraints.forEach((item, index) => {
      const path = '$.constraints[' + index + ']';
      if (!exactFields(item, ['constraint_id', 'kind', 'candidate_id', 'active'], path, errors)) return;
      if (typeof item.constraint_id !== 'string' || !ID_RE.test(item.constraint_id)) errors.push('INVALID_IDENTIFIER:' + path + '.constraint_id');
      if (constraints.has(item.constraint_id)) errors.push('DUPLICATE_CONSTRAINT_ID:' + path + '.constraint_id');
      if (item.kind !== 'FORBID_CANDIDATE') errors.push('UNSUPPORTED_CONSTRAINT_KIND:' + path + '.kind');
      if (item.candidate_id !== '*' && !new Set(candidates).has(item.candidate_id)) errors.push('UNKNOWN_CONSTRAINT_CANDIDATE:' + path + '.candidate_id');
      if (typeof item.active !== 'boolean') errors.push('EXPECTED_BOOLEAN:' + path + '.active');
      constraints.set(item.constraint_id, {...item});
      });
    }

    const boundary = document.boundary;
    if (!exactFields(boundary, ['expected_observation_ids', 'expected_evidence_ids'], '$.boundary', errors)) return [null, uniqueSorted(errors)];
    const expectedObservationIds = uniqueStrings(boundary.expected_observation_ids, '$.boundary.expected_observation_ids', errors);
    const expectedEvidenceIds = uniqueStrings(boundary.expected_evidence_ids, '$.boundary.expected_evidence_ids', errors);
    const extraObservations = [...observations.keys()].filter(id => !new Set(expectedObservationIds).has(id)).sort(compareScalarSequence);
    const extraEvidence = [...evidence.keys()].filter(id => !new Set(expectedEvidenceIds).has(id)).sort(compareScalarSequence);
    if (extraObservations.length) errors.push('UNDECLARED_OBSERVATION:' + extraObservations.join(','));
    if (extraEvidence.length) errors.push('UNDECLARED_EVIDENCE:' + extraEvidence.join(','));
    if (errors.length) return [null, uniqueSorted(errors)];

    return [{
      schema: INPUT_SCHEMA,
      context: {
        context_id: context.context_id,
        question_id: context.question_id,
        domain: context.domain,
        candidate_ids: [...candidates].sort(compareScalarSequence),
        ruleset_id: context.ruleset_id,
        profile_id: context.profile_id,
        text_profile_id: context.text_profile_id,
        evidence_mode: context.evidence_mode,
        authority_mode: context.authority_mode,
        boundary_state: context.boundary_state,
      },
      sources: [...sources.values()].sort((a,b)=>compareScalarSequence(a.source_id,b.source_id)),
      evidence: [...evidence.values()].sort((a,b)=>compareScalarSequence(a.evidence_id,b.evidence_id)),
      observations: [...observations.values()].sort((a,b)=>compareScalarSequence(a.observation_id,b.observation_id)),
      constraints: [...constraints.values()].sort((a,b)=>compareScalarSequence(a.constraint_id,b.constraint_id)),
      boundary: {expected_observation_ids:[...expectedObservationIds].sort(compareScalarSequence), expected_evidence_ids:[...expectedEvidenceIds].sort(compareScalarSequence)},
    }, []];
  }

  function candidateMetrics(normalized) {
    const sourceMap = new Map(normalized.sources.map(item => [item.source_id, item]));
    const table = {};
    for (const candidate of normalized.context.candidate_ids) {
      const related = normalized.observations.filter(item => item.candidate_id === candidate);
      const support = related.filter(item => item.stance === 'SUPPORT');
      const oppose = related.filter(item => item.stance === 'OPPOSE');
      const abstain = related.filter(item => item.stance === 'ABSTAIN');
      const sourceIds = new Set(support.map(item => item.source_id));
      const families = new Set([...sourceIds].map(id => sourceMap.get(id).source_family));
      const classes = new Set([...sourceIds].map(id => sourceMap.get(id).source_class));
      const missingClasses = [...REQUIRED_CLASSES].filter(value => !classes.has(value)).sort(compareScalarSequence);
      const evidenceComplete = support.every(item => item.evidence_ids.length > 0);
      table[candidate] = {
        support_observation_ids:support.map(item=>item.observation_id).sort(compareScalarSequence),
        opposition_observation_ids:oppose.map(item=>item.observation_id).sort(compareScalarSequence),
        abstention_observation_ids:abstain.map(item=>item.observation_id).sort(compareScalarSequence),
        support_source_count:sourceIds.size,
        support_family_count:families.size,
        support_classes:[...classes].sort(compareScalarSequence),
        missing_required_classes:missingClasses,
        missing_support_sources:Math.max(0,3-sourceIds.size),
        missing_source_families:Math.max(0,3-families.size),
        evidence_complete:evidenceComplete,
        eligible:support.length > 0 && sourceIds.size >= 3 && families.size >= 3 && missingClasses.length === 0 && evidenceComplete,
      };
    }
    return table;
  }

  function minimalWitness(normalized, candidate) {
    const sourceMap = new Map(normalized.sources.map(item => [item.source_id, item]));
    const representative = new Map();
    const orderedSupport = normalized.observations
      .filter(item => item.candidate_id === candidate && item.stance === 'SUPPORT' && item.evidence_ids.length)
      .sort((a,b)=>compareScalarSequence(a.observation_id,b.observation_id));
    for (const observation of orderedSupport) if (!representative.has(observation.source_id)) representative.set(observation.source_id, observation);

    const requiredOrder = ['MODEL','MODEL_REVIEW','RULE_CHECK'];
    const classBits = new Map(requiredOrder.map((value,index)=>[value,1 << index]));
    const targetMask = (1 << requiredOrder.length) - 1;
    const items = [...representative.entries()].map(([sourceId,observation]) => {
      const source = sourceMap.get(sourceId);
      return [observation.observation_id, source.source_family, classBits.get(source.source_class) || 0];
    }).sort((a,b)=>compareScalarSequence(a[0],b[0]));

    let states = new Map([['0||0', {mask:0, families:[], count:0, selected:[]}]]);
    for (const [observationId,family,classBit] of items) {
      const next = new Map(states);
      for (const state of states.values()) {
        let families = null;
        if (state.families !== null) {
          const familySet = new Set(state.families);
          familySet.add(family);
          families = familySet.size >= 3 ? null : [...familySet].sort(compareScalarSequence);
        }
        const selected = state.selected.concat([observationId]);
        const mask = state.mask | classBit;
        const count = Math.min(3, state.count + 1);
        const key = mask + '|' + (families === null ? '*' : families.join(',')) + '|' + count;
        const current = next.get(key);
        if (!current || selected.length < current.selected.length || (selected.length === current.selected.length && selected.join('\u0000') < current.selected.join('\u0000'))) {
          next.set(key,{mask,families,count,selected});
        }
      }
      states = next;
    }
    const finalState = states.get(targetMask + '|*|3');
    return finalState ? finalState.selected : [];
  }

  function result(state, reason, candidate, eligible, supported, witnessIds, blockers, repairs, metrics) {
    return {state, reason_code:reason, candidate_id:candidate, eligible_candidate_ids:eligible, supported_candidate_ids:supported, witness_observation_ids:witnessIds, blockers, repair_requirements:repairs, candidate_metrics:metrics, authority:'NONE'};
  }

  function decide(normalized) {
    const table = candidateMetrics(normalized);
    const supported = Object.keys(table).filter(candidate=>table[candidate].support_observation_ids.length).sort(compareScalarSequence);
    const eligible = Object.keys(table).filter(candidate=>table[candidate].eligible).sort(compareScalarSequence);
    const denial = [];
    for (const constraint of normalized.constraints) {
      if (!constraint.active) continue;
      const affected = constraint.candidate_id === '*' ? supported : (supported.includes(constraint.candidate_id) ? [constraint.candidate_id] : []);
      if (affected.length) denial.push('ACTIVE_PROHIBITION:' + constraint.constraint_id + ':' + affected.sort(compareScalarSequence).join(','));
    }
    if (denial.length) return result('DENIED','ACTIVE_PROHIBITION',null,eligible,supported,[],denial.sort(compareScalarSequence),[],table);

    const supportBySource = new Map();
    const opposeBySource = new Map();
    for (const item of normalized.observations) {
      const map = item.stance === 'SUPPORT' ? supportBySource : (item.stance === 'OPPOSE' ? opposeBySource : null);
      if (!map) continue;
      if (!map.has(item.source_id)) map.set(item.source_id, new Set());
      map.get(item.source_id).add(item.candidate_id);
    }
    const sourceBlockers = [];
    for (const [source,candidates] of [...supportBySource.entries()].sort((a,b)=>compareScalarSequence(a[0],b[0]))) if (candidates.size > 1) sourceBlockers.push('SOURCE_MULTI_CANDIDATE_SUPPORT:' + source);
    for (const source of [...supportBySource.keys()].filter(id=>opposeBySource.has(id)).sort(compareScalarSequence)) if ([...supportBySource.get(source)].some(candidate=>opposeBySource.get(source).has(candidate))) sourceBlockers.push('SOURCE_SUPPORT_OPPOSE_CONFLICT:' + source);
    if (sourceBlockers.length) return result('ABSTAIN','SOURCE_CONFLICT',null,eligible,supported,[],uniqueSorted(sourceBlockers),[],table);
    if (eligible.length > 1) return result('ABSTAIN','MULTIPLE_ELIGIBLE_CANDIDATES',null,eligible,supported,[],['MULTIPLE_ELIGIBLE_CANDIDATES:' + eligible.join(',')],[],table);
    if (eligible.length === 1) {
      const winner = eligible[0];
      const blockers = [];
      if (table[winner].opposition_observation_ids.length) blockers.push('OPPOSITION_PRESENT:' + table[winner].opposition_observation_ids.join(','));
      const minority = supported.filter(candidate=>candidate!==winner).sort(compareScalarSequence);
      if (minority.length) blockers.push('MINORITY_SUPPORT_PRESENT:' + minority.join(','));
      if (blockers.length) return result('ABSTAIN','BLOCKING_DISAGREEMENT',null,eligible,supported,[],blockers.sort(compareScalarSequence),[],table);
    }
    if (eligible.length === 0 && supported.length > 1) return result('ABSTAIN','COMPETING_PARTIAL_SUPPORT',null,[],supported,[],['COMPETING_PARTIAL_SUPPORT:' + supported.join(',')],[],table);

    const repairs = [];
    if (normalized.context.boundary_state !== 'SEALED') repairs.push('SEAL_DECLARED_BOUNDARY');
    const presentObs = new Set(normalized.observations.map(item=>item.observation_id));
    const presentEvidence = new Set(normalized.evidence.map(item=>item.evidence_id));
    const missingObs = normalized.boundary.expected_observation_ids.filter(id=>!presentObs.has(id)).sort(compareScalarSequence);
    const missingEvidence = normalized.boundary.expected_evidence_ids.filter(id=>!presentEvidence.has(id)).sort(compareScalarSequence);
    if (missingObs.length) repairs.push('SUPPLY_OBSERVATIONS:' + missingObs.join(','));
    if (missingEvidence.length) repairs.push('SUPPLY_EVIDENCE:' + missingEvidence.join(','));
    if (repairs.length) return result('INCOMPLETE','BOUNDARY_INCOMPLETE',null,eligible,supported,[],[],repairs.sort(compareScalarSequence),table);
    if (eligible.length === 1) return result('RESOLVED','UNIQUE_ADMISSIBLE_CANDIDATE',eligible[0],[eligible[0]],supported,minimalWitness(normalized,eligible[0]),[],[],table);

    for (const candidate of (supported.length ? supported : normalized.context.candidate_ids)) {
      const item = table[candidate];
      if (item.missing_support_sources) repairs.push('ADD_SUPPORT_SOURCES:' + candidate + ':' + item.missing_support_sources);
      if (item.missing_source_families) repairs.push('ADD_SOURCE_FAMILIES:' + candidate + ':' + item.missing_source_families);
      if (item.missing_required_classes.length) repairs.push('ADD_REQUIRED_CLASSES:' + candidate + ':' + item.missing_required_classes.join(','));
      if (!item.evidence_complete) repairs.push('ATTACH_EVIDENCE_TO_SUPPORT:' + candidate);
    }
    return result('INCOMPLETE','ADMISSION_REQUIREMENTS_UNMET',null,[],supported,[],[],uniqueSorted(repairs),table);
  }

  async function resolveDocument(document) {
    const submitted = await taggedHash('ORL-AI-SUBMITTED-INPUT-5', document);
    const [normalized, errors] = normalize(document);
    let core;
    if (errors.length) {
      core = {
        schema:BUNDLE_SCHEMA, project:PROJECT, version:VERSION, context_id:null, ruleset_id:RULESET_ID, profile_id:PROFILE_ID, text_profile_id:TEXT_PROFILE_ID, boundary_state:null, normalized_input:null,
        resolution:result('REFUSED','STRUCTURAL_INTAKE_REFUSAL',null,[],[],[],errors,[],{}),
        counts:{candidates:0,sources:0,evidence:0,observations:0,constraints:0},
        commitments:{submitted_input_commitment:submitted,normalized_input_commitment:null,observation_set_commitment:null,evidence_set_commitment:null,constraint_set_commitment:null,witness_commitment:await taggedHash('ORL-AI-WITNESS-SET-5',[])},
      };
    } else {
      const resolution = decide(normalized);
      core = {
        schema:BUNDLE_SCHEMA, project:PROJECT, version:VERSION, context_id:normalized.context.context_id, ruleset_id:normalized.context.ruleset_id, profile_id:normalized.context.profile_id, text_profile_id:normalized.context.text_profile_id, boundary_state:normalized.context.boundary_state, normalized_input:normalized, resolution,
        counts:{candidates:normalized.context.candidate_ids.length,sources:normalized.sources.length,evidence:normalized.evidence.length,observations:normalized.observations.length,constraints:normalized.constraints.length},
        commitments:{submitted_input_commitment:submitted,normalized_input_commitment:await taggedHash('ORL-AI-NORMALIZED-INPUT-5',normalized),observation_set_commitment:await taggedHash('ORL-AI-OBSERVATION-SET-5',normalized.observations),evidence_set_commitment:await taggedHash('ORL-AI-EVIDENCE-SET-5',normalized.evidence),constraint_set_commitment:await taggedHash('ORL-AI-CONSTRAINT-SET-5',normalized.constraints),witness_commitment:await taggedHash('ORL-AI-WITNESS-SET-5',resolution.witness_observation_ids)},
      };
    }
    const resolutionId = await taggedHash('ORL-AI-DECISION-RESOLUTION-ID-5',{context_id:core.context_id,ruleset_id:core.ruleset_id,profile_id:core.profile_id,text_profile_id:core.text_profile_id,boundary_state:core.boundary_state,resolution:core.resolution,structural_commitments:{normalized_input_commitment:core.commitments.normalized_input_commitment,observation_set_commitment:core.commitments.observation_set_commitment,evidence_set_commitment:core.commitments.evidence_set_commitment,constraint_set_commitment:core.commitments.constraint_set_commitment,witness_commitment:core.commitments.witness_commitment}});
    const artifactProfile = {profile_id:ARTIFACT_PROFILE_ID,identity_algorithm:'SHA-256',canonicalization:'UTF-8 sorted-key compact JSON with LF terminator'};
    const bundleId = await taggedHash('ORL-AI-PRIVATE-BUNDLE-ID-5',{...core,decision_resolution_id:resolutionId,artifact_profile:artifactProfile});
    const bundle = {...core,artifact_profile:artifactProfile,identities:{decision_resolution_id:resolutionId,private_bundle_id:bundleId}};
    const receiptCore = {schema:RECEIPT_SCHEMA,project:PROJECT,version:VERSION,context_id:bundle.context_id,ruleset_id:bundle.ruleset_id,profile_id:bundle.profile_id,text_profile_id:bundle.text_profile_id,state:bundle.resolution.state,reason_code:bundle.resolution.reason_code,candidate_id:bundle.resolution.candidate_id,authority:'NONE',boundary_state:bundle.boundary_state,counts:bundle.counts,commitments:bundle.commitments,decision_resolution_id:resolutionId,private_bundle_id:bundleId};
    const receipt = {...receiptCore,public_receipt_id:await taggedHash('ORL-AI-PUBLIC-RECEIPT-ID-5',receiptCore)};
    bundle.identities.public_receipt_id = receipt.public_receipt_id;
    return {bundle,receipt};
  }

  return {PROJECT,VERSION,INPUT_SCHEMA,BUNDLE_SCHEMA,RECEIPT_SCHEMA,RULESET_ID,PROFILE_ID,TEXT_PROFILE_ID,ARTIFACT_PROFILE_ID,canonicalText,compareScalarSequence,normalize,decide,resolveDocument,sha256HexPure,sha256Hex,hashBackendName};
})();

if (typeof module !== 'undefined' && module.exports) module.exports = ORL_AI;
if (typeof window !== 'undefined') window.ORL_AI = ORL_AI;

if (typeof require !== 'undefined' && require.main === module) {
  const fs = require('fs');
  const path = require('path');
  const {strictJsonParseBytes, ParserRefusal} = require('./ORL_AI_Strict_Json_v5_0_0.js');
  const args = process.argv.slice(2);
  const value = flag => { const i=args.indexOf(flag); return i>=0 ? args[i+1] : null; };
  (async()=>{
    if (args.includes('--self-test')) {
      const root = path.resolve(__dirname,'..');
      const manifest = strictJsonParseBytes(fs.readFileSync(path.join(root,'corpus','ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json')));
      let passed=0;
      for (const entry of manifest.entries) {
        const input = strictJsonParseBytes(fs.readFileSync(path.join(root,entry.input_path)));
        const expectedBundle = fs.readFileSync(path.join(root,entry.bundle_path),'utf8');
        const expectedReceipt = fs.readFileSync(path.join(root,entry.receipt_path),'utf8');
        const actual = await ORL_AI.resolveDocument(input);
        const ok = ORL_AI.canonicalText(actual.bundle)===expectedBundle && ORL_AI.canonicalText(actual.receipt)===expectedReceipt;
        console.log((ok?'PASS':'FAIL')+'  '+entry.case_id);
        if (ok) passed++;
      }
      console.log('TOTAL '+passed+'/'+manifest.entries.length+' PASS');
      process.exitCode = passed===manifest.entries.length ? 0 : 1;
      return;
    }
    const inputPath=value('--resolve');
    if (!inputPath) { console.log('Use --self-test or --resolve <input> [--output <bundle>] [--receipt-output <receipt>]'); return; }
    let input;
    try {
      input = strictJsonParseBytes(fs.readFileSync(inputPath));
    } catch (error) {
      const code = error instanceof ParserRefusal ? error.code : String(error);
      console.error('PARSER REFUSAL: ' + code);
      process.exitCode = 2;
      return;
    }
    const actual=await ORL_AI.resolveDocument(input);
    const output=value('--output');
    const receiptOutput=value('--receipt-output');
    if (output) fs.writeFileSync(output,ORL_AI.canonicalText(actual.bundle),'utf8'); else process.stdout.write(ORL_AI.canonicalText(actual.bundle));
    if (receiptOutput) fs.writeFileSync(receiptOutput,ORL_AI.canonicalText(actual.receipt),'utf8');
  })().catch(error=>{console.error(error.stack||String(error));process.exitCode=1;});
}
