/** Public signed transaction recovery only. Never store a bearer session or private key. */
import {bytes,b58encode,explorer} from './core.mjs';
import {decodeLegacy} from './wire.mjs';

export function parsePending(stored,{jobId,origin,programId}) {
 try {
  if(typeof stored!=='string'||stored.length>4096)return null;
  const p=JSON.parse(stored);
  if(!p||p.job_id!==jobId||!['fund','refund'].includes(p.action)||!explorer('devnet',p.signature))return null;
  if(p.transaction_base64) {
   const tx=decodeLegacy(bytes(p.transaction_base64));
   if(p.version!==1||p.origin!==origin||p.program_id!==programId||tx.payer!==p.address||tx.instructions[0].program!==p.program_id||b58encode(tx.signature)!==p.signature)return null;
  }
  return p;
 } catch {return null;}
}

export async function recoverPending(p,request) {
 const path=`/api/jobs/${encodeURIComponent(p.job_id)}`;
 const confirmation={action:p.action,signature:p.signature};
 try {return await request(`${path}/confirm`,confirmation);}
 catch(error) {
  if(!p.transaction_base64)throw error;
  // Check first, then retry the original bytes. The API independently validates the exact action.
  await request(`${path}/broadcast`,{action:p.action,transaction_base64:p.transaction_base64});
  return await request(`${path}/confirm`,confirmation);
 }
}
