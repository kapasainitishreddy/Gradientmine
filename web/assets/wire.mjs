/** Strict legacy-message inspector. Program PDAs are enforced by the on-chain program.
 * This is not a general Solana SDK: only this protocol's bounded, single-instruction messages. */
import {bytes,b58decode,b58encode,hex,sha256,equal} from './core.mjs';
const SYSTEM='11111111111111111111111111111111';
const require=(condition,text)=>{if(!condition)throw Error(text);};
const unhex=s=>{require(/^[a-f0-9]{64}$/.test(s),'Invalid evidence hash');return Uint8Array.from(s.match(/../g),x=>parseInt(x,16));};
export function decodeLegacy(raw) {
 require(raw instanceof Uint8Array && raw.length>=100 && raw.length<=1232,'Unsupported transaction size');
 let p=0;
 const take=n=>{require(p+n<=raw.length,'Truncated transaction');const a=raw.slice(p,p+n);p+=n;return a;};
 const small=()=>{let n=0,shift=0;for(let i=0;i<3;i++){const b=take(1)[0];n+=(b&127)*2**shift; if(!(b&128)){require(i===0 || b!==0,'Noncanonical length');return n;}shift+=7;}throw Error('Invalid compact length');};
 require(small()===1,'Exactly one wallet signature is supported');const signature=take(64);const start=p;
 const h=take(3);require(h[0]===1 && h[1]===0,'Only a single writable fee-payer signer is supported');
 const count=small();require(count>=2&&count<=8&&h[2]<count,'Unsupported account count');
 const keys=Array.from({length:count},()=>b58encode(take(32)));
 require(new Set(keys).size===keys.length,'Duplicate account key');
 const blockhash=b58encode(take(32));require(small()===1,'Extra instructions are not permitted');
 const programIndex=take(1)[0];require(programIndex<count,'Invalid program index');
 const accountCount=small();require(accountCount>=2&&accountCount<=4,'Invalid instruction account count');
 const accounts=Array.from(take(accountCount),i=>{require(i<count,'Invalid account index');return{address:keys[i],signer:i===0,writable:i<count-h[2]};});
 const data=take(small());require(p===raw.length,'Trailing transaction data');
 const program=keys[programIndex];require(programIndex>=count-h[2] && programIndex!==0,'Program must be read-only');
 require(new Set([...accounts.map(a=>a.address),program]).size===count,'Unexpected account keys');
 return{payer:keys[0],blockhash,signature,message:raw.slice(start),instructions:[{program,accounts,data}]};
}
function le64(value){require(Number.isSafeInteger(value)&&value>=0,'Unsafe policy integer');const a=new Uint8Array(8);new DataView(a.buffer).setBigUint64(0,BigInt(value),true);return a;}
export async function validateIntent(intent,action,job,config,address,sub=null) {
 const p=job.policy;
 require(config.mode==='devnet' && config.program_id && config.program_id!==SYSTEM,'Not a configured Devnet deployment');
 require(intent.action===action && intent.chain==='solana:devnet' && intent.program_id===config.program_id && p.program_id===config.program_id,'Program or network mismatch');
 require(intent.payer===address && address===(action==='register'?sub?.worker:job.creator),'Wrong transaction payer');
 require(Number.isSafeInteger(intent.fee_lamports)&&intent.fee_lamports>=0&&intent.fee_lamports<=100000,'Unexpected network fee');
 require(Number.isSafeInteger(intent.rent_lamports)&&intent.rent_lamports>=0&&intent.rent_lamports<=100000000,'Unexpected account rent');
 const tx=decodeLegacy(bytes(intent.transaction_base64));
 require(tx.signature.every(v=>v===0),'Expected an unsigned transaction');
 let expectedData, expectedAccounts;
 const a=(address,signer,writable)=>({address,signer,writable});
 if(action==='fund'){
  expectedData=new Uint8Array([0,...unhex(await sha256(new TextEncoder().encode(job.id))),...unhex(job.policy_sha256),...b58decode(p.validator),...le64(p.deadline),...le64(p.refund_after),...le64(p.reward_lamports)]);
  expectedAccounts=[a(address,true,true),a(job.bounty_address,false,true),a(SYSTEM,false,false)];
  require(intent.reward_lamports===p.reward_lamports,'Reward differs from bounty policy');
 }else if(action==='refund'){
  expectedData=new Uint8Array([3]);expectedAccounts=[a(address,true,true),a(job.bounty_address,false,true)];
  require(intent.reward_lamports===0 && intent.rent_lamports===0,'Unexpected refund costs');
 }else if(action==='register'&&sub){
  expectedData=new Uint8Array([1,...unhex(sub.artifact_sha256),...unhex(sub.manifest_sha256)]);
  require(intent.accounts.length===4&&b58decode(intent.accounts[2].address).length===32,'Invalid submission account');
  expectedAccounts=[a(address,true,true),a(job.bounty_address,false,true),a(intent.accounts[2].address,false,true),a(SYSTEM,false,false)];
  require(intent.reward_lamports===0,'Unexpected registration reward debit');
 }else throw Error('Unsupported wallet action');
 const ix=tx.instructions[0];
 require(tx.payer===address&&ix.program===config.program_id&&equal(ix.accounts,expectedAccounts)&&equal(intent.accounts,expectedAccounts),'Transaction account permissions differ from the reviewed action');
 require(hex(ix.data)===hex(expectedData)&&hex(bytes(intent.instruction_base64))===hex(expectedData),'Transaction data differs from the bounty policy');
 return tx;
}
export async function validateWalletSignature(unsigned,signed,address){
 const a=decodeLegacy(unsigned),b=decodeLegacy(signed);
 require(hex(a.message)===hex(b.message)&&b.payer===address,'Wallet changed the reviewed transaction; refusing to broadcast');
 const key=await crypto.subtle.importKey('raw',b58decode(address),'Ed25519',false,['verify']);
 require(await crypto.subtle.verify('Ed25519',key,b.signature,b.message),'Wallet transaction signature is invalid');
 return b58encode(b.signature);
}
