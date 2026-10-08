export const THEMES = Object.freeze({
  void: Object.freeze({label:'Void', meta:'#efebe3', hint:'Editorial mineral stone and evidence gallery'}),
  aurora: Object.freeze({label:'Aurora', meta:'#efebe3', hint:'Editorial mineral stone and evidence gallery'}),
  paper: Object.freeze({label:'Paper', meta:'#efebe3', hint:'Editorial mineral stone and evidence gallery'}),
});
export const THEME_ORDER = Object.freeze(['void','aurora','paper']);

export function normalizeTheme(value){
  return Object.prototype.hasOwnProperty.call(THEMES, value) ? value : 'void';
}
export function nextTheme(value){
  const current=normalizeTheme(value),index=THEME_ORDER.indexOf(current);
  return THEME_ORDER[(index+1)%THEME_ORDER.length];
}
export function themeMetaColor(value){return THEMES[normalizeTheme(value)].meta;}
export function readTheme(storage=globalThis.localStorage){
  try{return normalizeTheme(storage?.getItem('gradientmine-theme'));}catch{return 'void';}
}
export function writeTheme(value,storage=globalThis.localStorage){
  const theme=normalizeTheme(value);
  try{storage?.setItem('gradientmine-theme',theme);}catch{}
  return theme;
}
export function applyTheme(value,doc=globalThis.document){
  const theme=normalizeTheme(value);
  if(doc?.documentElement)doc.documentElement.dataset.theme=theme;
  const meta=doc?.querySelector?.('meta[name="theme-color"]');
  if(meta)meta.setAttribute('content',themeMetaColor(theme));
  return theme;
}
