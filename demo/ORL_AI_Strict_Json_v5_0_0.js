'use strict';

const ORL_AI_STRICT_JSON = (() => {
  const MAX_EXACT_INTEGER = 9007199254740991n;

  class ParserRefusal extends Error {
    constructor(code) {
      super(code);
      this.name = 'ParserRefusal';
      this.code = code;
    }
  }

  const isWhitespace = code => code === 0x20 || code === 0x09 || code === 0x0a || code === 0x0d;
  const isDigit = code => code >= 0x30 && code <= 0x39;
  const isHighSurrogate = code => code >= 0xd800 && code <= 0xdbff;
  const isLowSurrogate = code => code >= 0xdc00 && code <= 0xdfff;

  class StrictParser {
    constructor(text) {
      this.text = text;
      this.length = text.length;
      this.position = 0;
    }

    refuse(code) {
      throw new ParserRefusal(code);
    }

    peek(offset = 0) {
      const index = this.position + offset;
      return index < this.length ? this.text.charCodeAt(index) : -1;
    }

    skipWhitespace() {
      while (this.position < this.length && isWhitespace(this.peek())) this.position += 1;
    }

    parseValue() {
      const code = this.peek();
      if (code === -1) this.refuse('MALFORMED_JSON:unexpected end of input');
      if (code === 0x7b) return this.parseObject();
      if (code === 0x5b) return this.parseArray();
      if (code === 0x22) return this.parseString();
      if (code === 0x2d || isDigit(code)) return this.parseNumber();
      if (code === 0x74) return this.parseLiteral('true', true);
      if (code === 0x66) return this.parseLiteral('false', false);
      if (code === 0x6e) return this.parseLiteral('null', null);
      if (code === 0x4e) this.refuse('NONFINITE_JSON_NUMBER:NaN');
      if (code === 0x49) this.refuse('NONFINITE_JSON_NUMBER:Infinity');
      this.refuse('MALFORMED_JSON:unexpected character at ' + this.position);
    }

    parseLiteral(word, value) {
      if (this.text.slice(this.position, this.position + word.length) !== word) {
        this.refuse('MALFORMED_JSON:invalid literal at ' + this.position);
      }
      this.position += word.length;
      return value;
    }

    parseObject() {
      this.position += 1;
      const result = Object.create(null);
      const keys = new Set();
      this.skipWhitespace();
      if (this.peek() === 0x7d) {
        this.position += 1;
        return result;
      }
      for (;;) {
        this.skipWhitespace();
        if (this.peek() !== 0x22) this.refuse('MALFORMED_JSON:expected string key at ' + this.position);
        const key = this.parseString();
        if (keys.has(key)) this.refuse('DUPLICATE_JSON_KEY:' + key);
        keys.add(key);
        this.skipWhitespace();
        if (this.peek() !== 0x3a) this.refuse('MALFORMED_JSON:expected colon at ' + this.position);
        this.position += 1;
        this.skipWhitespace();
        result[key] = this.parseValue();
        this.skipWhitespace();
        const separator = this.peek();
        if (separator === 0x2c) {
          this.position += 1;
          continue;
        }
        if (separator === 0x7d) {
          this.position += 1;
          return result;
        }
        this.refuse('MALFORMED_JSON:expected comma or end of object at ' + this.position);
      }
    }

    parseArray() {
      this.position += 1;
      const result = [];
      this.skipWhitespace();
      if (this.peek() === 0x5d) {
        this.position += 1;
        return result;
      }
      for (;;) {
        this.skipWhitespace();
        result.push(this.parseValue());
        this.skipWhitespace();
        const separator = this.peek();
        if (separator === 0x2c) {
          this.position += 1;
          continue;
        }
        if (separator === 0x5d) {
          this.position += 1;
          return result;
        }
        this.refuse('MALFORMED_JSON:expected comma or end of array at ' + this.position);
      }
    }

    parseUnicodeEscape() {
      const start = this.position;
      const hex = this.text.slice(this.position + 1, this.position + 5);
      if (!/^[0-9a-fA-F]{4}$/.test(hex)) this.refuse('MALFORMED_JSON:invalid unicode escape at ' + start);
      const first = parseInt(hex, 16);
      this.position += 5;
      if (isHighSurrogate(first)) {
        if (this.peek() !== 0x5c || this.peek(1) !== 0x75) this.refuse('MALFORMED_JSON:unpaired surrogate at ' + start);
        this.position += 1;
        const secondStart = this.position;
        const lowHex = this.text.slice(this.position + 1, this.position + 5);
        if (!/^[0-9a-fA-F]{4}$/.test(lowHex)) this.refuse('MALFORMED_JSON:invalid unicode escape at ' + secondStart);
        const second = parseInt(lowHex, 16);
        if (!isLowSurrogate(second)) this.refuse('MALFORMED_JSON:unpaired surrogate at ' + start);
        this.position += 5;
        return String.fromCodePoint(0x10000 + ((first - 0xd800) << 10) + (second - 0xdc00));
      }
      if (isLowSurrogate(first)) this.refuse('MALFORMED_JSON:unpaired surrogate at ' + start);
      return String.fromCharCode(first);
    }

    parseString() {
      this.position += 1;
      let output = '';
      for (;;) {
        if (this.position >= this.length) this.refuse('MALFORMED_JSON:unterminated string');
        const code = this.peek();
        if (code === 0x22) {
          this.position += 1;
          return output;
        }
        if (code === 0x5c) {
          this.position += 1;
          if (this.position >= this.length) this.refuse('MALFORMED_JSON:unterminated escape');
          const escape = this.peek();
          if (escape === 0x22) { output += '"'; this.position += 1; }
          else if (escape === 0x5c) { output += '\\'; this.position += 1; }
          else if (escape === 0x2f) { output += '/'; this.position += 1; }
          else if (escape === 0x62) { output += '\b'; this.position += 1; }
          else if (escape === 0x66) { output += '\f'; this.position += 1; }
          else if (escape === 0x6e) { output += '\n'; this.position += 1; }
          else if (escape === 0x72) { output += '\r'; this.position += 1; }
          else if (escape === 0x74) { output += '\t'; this.position += 1; }
          else if (escape === 0x75) output += this.parseUnicodeEscape();
          else this.refuse('MALFORMED_JSON:invalid escape at ' + this.position);
          continue;
        }
        if (code < 0x20) this.refuse('MALFORMED_JSON:control character in string at ' + this.position);
        if (isHighSurrogate(code)) {
          const low = this.peek(1);
          if (!isLowSurrogate(low)) this.refuse('MALFORMED_JSON:unpaired surrogate at ' + this.position);
          output += this.text.slice(this.position, this.position + 2);
          this.position += 2;
          continue;
        }
        if (isLowSurrogate(code)) this.refuse('MALFORMED_JSON:unpaired surrogate at ' + this.position);
        output += this.text[this.position];
        this.position += 1;
      }
    }

    parseNumber() {
      const start = this.position;
      if (this.peek() === 0x2d && this.peek(1) === 0x49) this.refuse('NONFINITE_JSON_NUMBER:-Infinity');
      if (this.peek() === 0x2d) this.position += 1;
      const integerStart = this.position;
      if (this.peek() === 0x30) {
        this.position += 1;
        if (isDigit(this.peek())) this.refuse('MALFORMED_JSON:leading zero at ' + start);
      } else if (this.peek() >= 0x31 && this.peek() <= 0x39) {
        while (isDigit(this.peek())) this.position += 1;
      } else {
        this.refuse('MALFORMED_JSON:invalid number at ' + start);
      }
      if (this.position === integerStart) this.refuse('MALFORMED_JSON:invalid number at ' + start);
      let floating = false;
      if (this.peek() === 0x2e) {
        floating = true;
        this.position += 1;
        if (!isDigit(this.peek())) this.refuse('MALFORMED_JSON:invalid fraction at ' + this.position);
        while (isDigit(this.peek())) this.position += 1;
      }
      if (this.peek() === 0x65 || this.peek() === 0x45) {
        floating = true;
        this.position += 1;
        if (this.peek() === 0x2b || this.peek() === 0x2d) this.position += 1;
        if (!isDigit(this.peek())) this.refuse('MALFORMED_JSON:invalid exponent at ' + this.position);
        while (isDigit(this.peek())) this.position += 1;
      }
      const token = this.text.slice(start, this.position);
      if (floating) this.refuse('FLOATING_JSON_NUMBER');
      let integer;
      try {
        integer = BigInt(token);
      } catch (error) {
        this.refuse('MALFORMED_JSON:invalid number at ' + start);
      }
      if (integer < -MAX_EXACT_INTEGER || integer > MAX_EXACT_INTEGER) this.refuse('INTEGER_OUTSIDE_EXACT_RANGE');
      return Number(integer);
    }
  }

  function strictJsonParse(text) {
    if (typeof text !== 'string') throw new ParserRefusal('MALFORMED_JSON:input is not a string');
    if (text.length > 0 && text.charCodeAt(0) === 0xfeff) throw new ParserRefusal('UTF8_BOM');
    const parser = new StrictParser(text);
    parser.skipWhitespace();
    const value = parser.parseValue();
    parser.skipWhitespace();
    if (parser.position !== parser.length) throw new ParserRefusal('MALFORMED_JSON:Extra data at ' + parser.position);
    return value;
  }

  function strictJsonParseBytes(bytes) {
    const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    if (view.length >= 3 && view[0] === 0xef && view[1] === 0xbb && view[2] === 0xbf) throw new ParserRefusal('UTF8_BOM');
    let text;
    try {
      text = new TextDecoder('utf-8', {fatal: true}).decode(view);
    } catch (error) {
      throw new ParserRefusal('INVALID_UTF8');
    }
    return strictJsonParse(text);
  }

  return {ParserRefusal, strictJsonParse, strictJsonParseBytes, MAX_EXACT_INTEGER};
})();

if (typeof module !== 'undefined' && module.exports) module.exports = ORL_AI_STRICT_JSON;
if (typeof window !== 'undefined') window.ORL_AI_STRICT_JSON = ORL_AI_STRICT_JSON;

if (typeof require !== 'undefined' && require.main === module) {
  const fs = require('fs');
  const path = require('path');
  const root = path.resolve(__dirname, '..');
  const {strictJsonParse, strictJsonParseBytes, ParserRefusal} = ORL_AI_STRICT_JSON;
  const args = process.argv.slice(2);
  const flagValue = flag => {
    const index = args.indexOf(flag);
    return index >= 0 ? args[index + 1] : null;
  };

  const classifyPath = flagValue('--classify');
  if (classifyPath) {
    try {
      strictJsonParseBytes(fs.readFileSync(classifyPath));
      console.log('ACCEPTED');
      process.exitCode = 0;
    } catch (error) {
      const code = error instanceof ParserRefusal ? error.code : String(error);
      console.log('PARSER REFUSAL: ' + code);
      process.exitCode = 2;
    }
  } else {
    const manifest = strictJsonParseBytes(fs.readFileSync(path.join(root, 'hostile', 'ORL_AI_Hostile_Corpus_Manifest_v5_0_0.json')));
    const checks = [];
    for (const entry of manifest.entries.filter(item => item.expected_parser_refusal)) {
      let observed = null;
      try {
        strictJsonParseBytes(fs.readFileSync(path.join(root, entry.path)));
      } catch (error) {
        observed = error instanceof ParserRefusal ? error.code : String(error);
      }
      checks.push(['refuse ' + entry.path + ' -> ' + entry.expected_parser_refusal, observed !== null && observed.includes(entry.expected_parser_refusal)]);
    }

    const wellFormedRoots = ['examples', 'corpus', 'capsules', 'parity', 'falsification', 'hostile/inputs'];
    const wellFormedPaths = [];
    const collect = directory => {
      for (const name of fs.readdirSync(directory)) {
        const fullPath = path.join(directory, name);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) collect(fullPath);
        else if (name.endsWith('.json')) wellFormedPaths.push(fullPath);
      }
    };
    for (const relative of wellFormedRoots) collect(path.join(root, relative));
    let allWellFormed = true;
    for (const filePath of wellFormedPaths) {
      try {
        const raw = fs.readFileSync(filePath);
        const strictValue = strictJsonParseBytes(raw);
        const ordinaryValue = JSON.parse(raw.toString('utf8'));
        if (JSON.stringify(strictValue) !== JSON.stringify(ordinaryValue)) allWellFormed = false;
      } catch (error) {
        allWellFormed = false;
      }
    }
    checks.push(['all shipped well-formed JSON parses identically to JSON.parse', allWellFormed]);

    const extras = [
      ['bare duplicate at top level', Buffer.from('{"a":1,"a":2}', 'utf8'), 'DUPLICATE_JSON_KEY'],
      ['exponent float', Buffer.from('{"a":1e3}', 'utf8'), 'FLOATING_JSON_NUMBER'],
      ['negative infinity', Buffer.from('{"a":-Infinity}', 'utf8'), 'NONFINITE_JSON_NUMBER'],
      ['leading zero', Buffer.from('{"a":01}', 'utf8'), 'MALFORMED_JSON'],
      ['max exact integer accepted', Buffer.from('{"a":9007199254740991}', 'utf8'), null],
      ['one past max refused', Buffer.from('{"a":9007199254740992}', 'utf8'), 'INTEGER_OUTSIDE_EXACT_RANGE'],
      ['valid surrogate pair accepted', Buffer.from('{"a":"\\ud83d\\ude00"}', 'utf8'), null],
      ['unpaired surrogate refused', Buffer.from('{"a":"\\ud800"}', 'utf8'), 'MALFORMED_JSON'],
    ];
    for (const [name, raw, expected] of extras) {
      let observed = null;
      try {
        strictJsonParseBytes(raw);
      } catch (error) {
        observed = error instanceof ParserRefusal ? error.code : String(error);
      }
      checks.push([name, expected === null ? observed === null : observed !== null && observed.includes(expected)]);
    }

    let passed = 0;
    for (const [name, ok] of checks) {
      if (ok) passed += 1;
      console.log((ok ? 'PASS' : 'FAIL') + '  ' + name);
    }
    console.log('TOTAL ' + passed + '/' + checks.length + ' PASS');
    process.exitCode = passed === checks.length ? 0 : 1;
  }
}
