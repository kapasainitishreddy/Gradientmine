import {base64, bytes, b58encode, messageChallenge, equal} from './core.mjs';
/** Wallet Standard discovery: original bounded adapter, no browser private-key handling. */
export class WalletSession {
  constructor(onChange) {
    this.wallets = new Set(); this.wallet = null; this.account = null; this.token = null; this.off = null; this.onChange = onChange; this.generation = 0;
    const api = Object.freeze({register: (...wallets) => {
      const added = wallets.filter(w => w?.features?.['standard:connect'] && w?.features?.['solana:signMessage']);
      added.forEach(w => this.wallets.add(w)); onChange();
      return () => {added.forEach(w => this.wallets.delete(w)); if(added.includes(this.wallet))this.clear(); onChange();};
    }});
    window.addEventListener('wallet-standard:register-wallet', event => { if (typeof event.detail === 'function') event.detail(api); });
    window.dispatchEvent(new CustomEvent('wallet-standard:app-ready', {detail:api}));
  }
  async connect(wallet, api) {
    this.clear();
    const generation=this.generation;
    const unchanged=()=>{if(generation!==this.generation)throw Error('Wallet connection changed or was cancelled. Connect again.');};
    const connected = await wallet.features['standard:connect'].connect();
    unchanged();
    const account = connected.accounts.find(a => a.chains?.includes('solana:devnet') && a.features?.includes('solana:signMessage'));
    if (!account) throw Error('Select a Solana Devnet-compatible account with message signing.');
    if (!(account.publicKey instanceof Uint8Array) || account.publicKey.length!==32 || b58encode(account.publicKey) !== account.address) throw Error('Wallet public key does not match its address.');
    const c = await api('/api/auth/challenge', {address:account.address});
    unchanged();
    const message = messageChallenge(c, location.origin, account.address);
    const [signed] = await wallet.features['solana:signMessage'].signMessage({account, message});
    unchanged();
    if (!equal([...signed.signedMessage], [...message]) || (signed.signatureType && signed.signatureType !== 'ed25519')) throw Error('Wallet modified the authentication message.');
    const session = await api('/api/auth/verify', {nonce:c.nonce, signature:base64(signed.signature)});
    unchanged();
    if(session.address!==account.address || typeof session.token!=='string' || !session.token)throw Error('Authentication session does not match the selected wallet.');
    this.wallet=wallet; this.account=account; this.token=session.token;
    this.off=wallet.features['standard:events']?.on('change', changes => {
      if(changes.accounts){
        const current=changes.accounts.find(a=>a.address===this.account?.address && a.publicKey instanceof Uint8Array && equal([...a.publicKey],[...this.account.publicKey]) && a.chains?.includes('solana:devnet') && a.features?.includes('solana:signMessage'));
        if(!current)this.disconnect(api).catch(()=>{});
        else {this.account=current;this.onChange();}
      }
    });
    this.onChange();
  }
  clear() { this.generation++; this.off?.(); this.off=null; this.wallet=null; this.account=null; this.token=null; }
  async disconnect(api) {
    // Start logout while the bearer is still available, then invalidate local state immediately.
    const logout=this.token?api('/api/auth/logout', {}):Promise.resolve();
    this.clear(); this.onChange();
    await logout;
  }
  async sign(intent) {
    const generation=this.generation,account=this.account;
    const feature=this.wallet?.features?.['solana:signTransaction'];
    if (!this.account?.features?.includes('solana:signTransaction') || !feature?.supportedTransactionVersions?.includes('legacy')) throw Error('This wallet cannot sign the supported legacy transaction. Use the worker CLI or another Wallet Standard wallet.');
    const [result]=await feature.signTransaction({account:this.account, chain:'solana:devnet', transaction:bytes(intent.transaction_base64)});
    if(generation!==this.generation || this.account!==account)throw Error('Wallet connection changed during approval. Review the transaction again.');
    return result.signedTransaction;
  }
}
