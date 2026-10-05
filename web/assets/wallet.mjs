import {base64, bytes, b58encode, messageChallenge, equal} from './core.mjs';
/** Wallet Standard discovery: original bounded adapter, no browser private-key handling. */
export class WalletSession {
  constructor(onChange) {
    this.wallets = new Set(); this.wallet = null; this.account = null; this.token = null; this.off = null; this.onChange = onChange;
    const api = Object.freeze({register: (...wallets) => {
      const added = wallets.filter(w => w?.features?.['standard:connect'] && w?.features?.['solana:signMessage']);
      added.forEach(w => this.wallets.add(w)); onChange();
      return () => {added.forEach(w => this.wallets.delete(w)); onChange();};
    }});
    window.addEventListener('wallet-standard:register-wallet', event => { if (typeof event.detail === 'function') event.detail(api); });
    window.dispatchEvent(new CustomEvent('wallet-standard:app-ready', {detail:api}));
  }
  async connect(wallet, api) {
    this.clear();
    const connected = await wallet.features['standard:connect'].connect();
    const account = connected.accounts.find(a => a.chains?.includes('solana:devnet') && a.features?.includes('solana:signMessage'));
    if (!account) throw Error('Select a Solana Devnet-compatible account with message signing.');
    if (b58encode(account.publicKey) !== account.address) throw Error('Wallet public key does not match its address.');
    const c = await api('/api/auth/challenge', {address:account.address});
    const message = messageChallenge(c, location.origin, account.address);
    const [signed] = await wallet.features['solana:signMessage'].signMessage({account, message});
    if (!equal([...signed.signedMessage], [...message]) || (signed.signatureType && signed.signatureType !== 'ed25519')) throw Error('Wallet modified the authentication message.');
    const session = await api('/api/auth/verify', {nonce:c.nonce, signature:base64(signed.signature)});
    this.wallet=wallet; this.account=account; this.token=session.token;
    this.off=wallet.features['standard:events']?.on('change', changes => {
      if (changes.accounts && !changes.accounts.some(a => a.address === this.account?.address)) { this.disconnect(api).catch(() => {}); }
    });
    this.onChange();
  }
  clear() { this.off?.(); this.off=null; this.wallet=null; this.account=null; this.token=null; }
  async disconnect(api) {
    try { if (this.token) await api('/api/auth/logout', {}); }
    finally { this.clear(); this.onChange(); }
  }
  async sign(intent) {
    const feature=this.wallet?.features?.['solana:signTransaction'];
    if (!this.account?.features?.includes('solana:signTransaction') || !feature?.supportedTransactionVersions?.includes('legacy')) throw Error('This wallet cannot sign the supported legacy transaction. Use the worker CLI or another Wallet Standard wallet.');
    const [result]=await feature.signTransaction({account:this.account, chain:'solana:devnet', transaction:bytes(intent.transaction_base64)});
    return result.signedTransaction;
  }
}
