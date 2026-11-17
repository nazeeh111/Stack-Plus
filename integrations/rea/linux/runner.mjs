// Own upstream and verify guest cleanup under Docker's bundled init reaper.
import {spawn} from 'node:child_process';
import {readdir,readFile,writeFile,mkdir} from 'node:fs/promises';
import {setTimeout} from 'node:timers/promises';
const out='/output';
await mkdir(out+'/home',{recursive:true});
const parent=Number((await readFile('/proc/self/status','utf8')).match(/^PPid:\s*(\d+)/m)?.[1]);
const initCommand=(await readFile('/proc/1/cmdline','utf8')).split('\0').filter(Boolean);
if(parent!==1||initCommand[0]!=='/sbin/docker-init')throw new Error('Expected owned Docker init ancestor; no process exclusion fallback');
const started=Date.now();
const child=spawn('/usr/local/bin/node',['/opt/rea/scripts/rea.mjs',...process.argv.slice(2)],{stdio:'inherit',env:process.env});
const result=await new Promise(resolve=>{
 child.once('error',error=>resolve({code:1,error:error.message}));
 child.once('exit',(code,signal)=>resolve({code,signal}));
});
async function inspect(){
 const rows=[];
 for(const name of await readdir('/proc')){
  if(!/^\d+$/.test(name)||Number(name)===process.pid||Number(name)===1)continue;
  try{
   const status=await readFile('/proc/'+name+'/status','utf8');
   const cmd=(await readFile('/proc/'+name+'/cmdline','utf8')).replaceAll('\0',' ');
   rows.push({pid:Number(name),state:status.match(/^State:\s*(.*)$/m)?.[1],command:cmd});
  }catch(error){if(error.code!=='ENOENT'&&error.code!=='ESRCH')throw error;}
 }
 return rows;
}
const observations=[];
let remaining=await inspect();observations.push(remaining);
const settleStart=Date.now();
while(remaining.length&&Date.now()-settleStart<2000){await setTimeout(50);remaining=await inspect();observations.push(remaining);}
const receipt={started,elapsed_ms:Date.now()-started,upstream:result,remaining_guest_processes:remaining,cleanup_complete:remaining.length===0,guest_pid:process.pid,init_ancestor:{pid:1,command:initCommand},reaping_observations:observations};
await writeFile(out+'/lifecycle.json',JSON.stringify(receipt,null,2)+'\n');
if(remaining.length)process.stderr.write('Owned REA process left guest processes; see lifecycle.json\n');
process.exitCode=result.code===0&&remaining.length===0?0:1;
