/** Python-compatible canonical JSON for bounded GradientMine signature payloads.
 * Python uses json.dumps(sort_keys=True,separators=(',', ':'),ensure_ascii=True,
 * allow_nan=False). Artifact schemas use integer numeric fields only.
 */
function quote(value) {
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g, ch =>
    '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'));
}

export function canonicalJson(value) {
  if (value === null) return 'null';
  if (typeof value === 'string') return quote(value);
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw Error('Non-finite JSON numbers are not allowed');
    // Signed artifact data is intentionally integer-only. Avoid JSON encoder
    // disagreements for integral-looking floats (Python prints 1.0, JS 1).
    if (!Number.isSafeInteger(value)) throw Error('Signed numeric fields must be safe integers');
    return String(value);
  }
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
  if (typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return '{' + keys.map(key => quote(key) + ':' + canonicalJson(value[key])).join(',') + '}';
  }
  throw Error('Unsupported signed JSON type');
}
