/** Public evidence utilities. No dependency, private key or external RPC in this module. */
const alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
export const bytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
export const base64 = a => btoa(String.fromCharCode(...a));
export const hex = a => [...a].map(x => x.toString(16).padStart(2, '0')).join('');
export const sha256 = async a => hex(new Uint8Array(await crypto.subtle.digest('SHA-256', a)));
export function b58decode(s) {
  if (typeof s !== 'string' || !s || s.length > 90) throw Error('Invalid base58');
  let n = 0n;
  for (const c of s) { const v = alphabet.indexOf(c); if (v < 0) throw Error('Invalid base58'); n = n * 58n + BigInt(v); }
  const result = []; while (n) { result.unshift(Number(n % 256n)); n /= 256n; }
  return new Uint8Array([...new Array(s.match(/^1*/)[0].length).fill(0), ...result]);
}
export function b58encode(a) {
  let n = 0n, out = ''; for (const b of a) n = n * 256n + BigInt(b);
  while (n) { out = alphabet[Number(n % 58n)] + out; n /= 58n; }
  let zeros = 0; while (zeros < a.length && a[zeros] === 0) zeros++;
  return '1'.repeat(zeros) + out;
}
export function solToLamports(value) {
  if (!/^(0|1)(\.\d{1,9})?$/.test(value)) throw Error('Enter 0 to 1 SOL, with at most 9 decimal places.');
  const [whole, fraction = ''] = value.split('.');
  const n = BigInt(whole) * 1000000000n + BigInt(fraction.padEnd(9, '0'));
  if (n > 1000000000n) throw Error('Maximum reward is 1 Devnet SOL.');
  return Number(n);
}
export function explorer(mode, value, kind = 'tx') {
  try { if (mode !== 'devnet' || !['tx','address'].includes(kind) || b58decode(value).length !== (kind === 'tx' ? 64 : 32)) return null; }
  catch { return null; }
  return `https://explorer.solana.com/${kind}/${value}?cluster=devnet`;
}
export function equal(a, b) {
  if (a === b) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
  const x = Object.keys(a).sort(), y = Object.keys(b).sort();
  return x.length === y.length && x.every((key, i) => key === y[i] && equal(a[key], b[key]));
}
export async function verifyEnvelope(envelope, expectedSigner) {
  try {
    if (!expectedSigner || envelope.signer !== expectedSigner || Object.keys(envelope).sort().join() !== 'payload,payload_base64,signature,signer') return false;
    const payload = bytes(envelope.payload_base64);
    if (!equal(JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(payload)), envelope.payload)) return false;
    const key = await crypto.subtle.importKey('raw', b58decode(expectedSigner), 'Ed25519', false, ['verify']);
    return await crypto.subtle.verify('Ed25519', key, bytes(envelope.signature), payload);
  } catch { return false; }
}
export const short = (s, n = 7) => s ? `${s.slice(0,n)}…${s.slice(-5)}` : 'Not available';
export const percent = x => typeof x === 'number' && Number.isFinite(x) ? `${(100*x).toFixed(2)}%` : 'Not evaluated';
export const delta = x => typeof x === 'number' && Number.isFinite(x) ? `${x >= 0 ? '+' : ''}${(100*x).toFixed(2)} pp` : 'Not evaluated';
export const lamports = n => `${(n / 1e9).toFixed(9).replace(/\.?0+$/, '') || '0'} SOL`;
export function node(tag, text, className) {
  const n = document.createElement(tag); if (text != null) n.textContent = text; if (className) n.className = className; return n;
}
export function messageChallenge(c, origin, address) {
  if (!/^[A-Za-z0-9_-]{43}$/.test(c.nonce) || !Number.isSafeInteger(c.expires_at) || c.expires_at <= Date.now()/1000 || c.expires_at > Date.now()/1000+360) throw Error('Authentication challenge does not match this origin, wallet or expiry.');
  const expected = `GradientMine wallet authentication v1\nOrigin: ${origin}\nWallet: ${address}\nNonce: ${c.nonce}\nExpires: ${c.expires_at}\nThis message authenticates a session. It does not authorize a transaction.`;
  if (c.message !== expected) throw Error('Refusing an unexpected authentication message.');
  return new TextEncoder().encode(expected);
}
