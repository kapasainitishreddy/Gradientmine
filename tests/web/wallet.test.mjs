import test from 'node:test';
import assert from 'node:assert/strict';
import {WalletSession} from '../../web/assets/wallet.mjs';
import {b58encode} from '../../web/assets/core.mjs';

globalThis.window = new EventTarget();
globalThis.CustomEvent = class extends Event { constructor(type, options) {super(type); this.detail = options.detail;} };
globalThis.location = {origin:'https://gradientmine.example'};

function fixture() {
  const publicKey=new Uint8Array(32).fill(3);
  const account={address:b58encode(publicKey),publicKey,chains:['solana:devnet'],features:['solana:signMessage','solana:signTransaction']};
  let release;
  const paused=new Promise(resolve=>{release=resolve;});
  const wallet={features:{'standard:connect':{connect:async()=>({accounts:[account]})},'solana:signMessage':{signMessage:async({message})=>{await paused;return [{signedMessage:message,signature:new Uint8Array(64),signatureType:'ed25519'}];}}}};
  const api=async(path,body)=>{
    if(path.endsWith('/challenge')) {
      const nonce='a'.repeat(43),expires_at=Math.floor(Date.now()/1000)+300;
      return {nonce,expires_at,message:`GradientMine wallet authentication v1\nOrigin: ${location.origin}\nWallet: ${body.address}\nNonce: ${nonce}\nExpires: ${expires_at}\nThis message authenticates a session. It does not authorize a transaction.`};
    }
    return {token:'test-session',address:account.address,expires_at:Math.floor(Date.now()/1000)+3600};
  };
  return {wallet,api,release,account};
}

test('disconnect invalidates an authentication request still waiting for wallet approval',async()=>{
 const {wallet,api,release}=fixture(),session=new WalletSession(()=>{});
 const connecting=session.connect(wallet,api);
 await new Promise(resolve=>setTimeout(resolve,0));
 session.clear();release();
 await assert.rejects(connecting,/changed|cancelled/i);
 assert.equal(session.token,null);assert.equal(session.account,null);
});

test('only the latest wallet connection may establish a session',async()=>{
 const first=fixture(),second=fixture(),session=new WalletSession(()=>{});
 const stale=session.connect(first.wallet,first.api);
 await new Promise(resolve=>setTimeout(resolve,0));
 const current=session.connect(second.wallet,second.api);second.release();await current;
 first.release();await assert.rejects(stale,/changed|cancelled/i);
 assert.equal(session.wallet,second.wallet);
});

test('a wallet change during transaction approval invalidates the returned signed bytes',async()=>{
 const {account}=fixture(),session=new WalletSession(()=>{});
 let complete;const wait=new Promise(resolve=>{complete=resolve;});
 session.account=account;
 session.wallet={features:{'solana:signTransaction':{supportedTransactionVersions:['legacy'],signTransaction:async()=>{await wait;return [{signedTransaction:new Uint8Array(100)}];}}}};
 const signing=session.sign({transaction_base64:Buffer.alloc(100).toString('base64')});
 session.clear();complete();
 await assert.rejects(signing,/changed during approval/);
});
