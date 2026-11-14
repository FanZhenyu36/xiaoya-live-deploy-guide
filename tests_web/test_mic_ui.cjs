const {test,afterEach}=require('node:test');const assert=require('node:assert/strict');
const vm=require('node:vm'),fs=require('node:fs');
if(!process.env.STAGE_HTML)throw Error('Set STAGE_HTML');
const html=fs.readFileSync(process.env.STAGE_HTML,'utf8');
const start=html.indexOf('const microphone = {');
const end=html.indexOf('$("btnMic").addEventListener',start);
const source=html.slice(start,end)+';microphone';
const instances=[];
afterEach(()=>{for(const m of instances)clearTimeout(m.timer);instances.length=0;});
function setup({permission,live=true}={}){
 const elements=new Map();const $=id=>{if(!elements.has(id))elements.set(id,{});return elements.get(id);};
 const calls=[],tracks=[{stopped:false,stop(){this.stopped=true;}}];const stream={getTracks:()=>tracks};
 class Recorder{
  static isTypeSupported(){return true;}
  constructor(){this.state='inactive';this.mimeType='audio/webm';}
  start(){this.state='recording';}
  stop(){this.state='inactive';this.ondataavailable?.({data:new Blob(['audio'])});queueMicrotask(()=>this.onstop?.());}
 }
 const context={$,state:{liveId:live?'test-live':null},window:{MediaRecorder:Recorder},MediaRecorder:Recorder,
  navigator:{mediaDevices:{getUserMedia:permission || (async()=>stream)}},Blob,AbortController,setTimeout,clearTimeout,
  api:async(path,opts)=>{calls.push(path);return {token:'test-token'};},toast:()=>{},
  fetch:async(path,opts)=>{calls.push(path);return {ok:true,json:async()=>({sent:true,text:'你好'})};}};
 const mic=vm.runInNewContext(source,context);instances.push(mic);
 return {mic,calls,tracks,stream,elements};
}
const tick=()=>new Promise(r=>setImmediate(r));
test('unconnected microphone never requests permission',async()=>{let permissionCalls=0;const {mic,calls}=setup({live:false,permission:async()=>{permissionCalls++;}});await mic.start();assert.equal(permissionCalls,0);assert.deepEqual(calls,[]);});
test('permission denial releases priority and restores controls',async()=>{const e=Object.assign(Error('denied'),{name:'NotAllowedError'});const {mic,calls,elements}=setup({permission:async()=>{throw e;}});await mic.start();assert.deepEqual(calls,['/api/mic/begin','/api/mic/cancel']);assert.equal(mic.busy,false);assert.equal(elements.get('btnMic').disabled,false);});
test('recording sends audio and releases physical tracks after stop',async()=>{const {mic,calls,tracks,elements}=setup();await mic.start();assert.equal(mic.recorder.state,'recording');mic.finish();await tick();await tick();assert.equal(tracks[0].stopped,true);assert.ok(calls.includes('/api/mic/audio'));assert.equal(mic.busy,false);assert.match(elements.get('micStatus').textContent,/已识别并发送/);});
test('cancellation while permission is pending stops a late stream and never uploads',async()=>{let grant;const {mic,calls,tracks,stream}=setup({permission:()=>new Promise(r=>grant=r)});const starting=mic.start();await tick();await mic.cancel();grant(stream);await starting;assert.equal(tracks[0].stopped,true);assert.equal(mic.busy,false);assert.equal(calls.includes('/api/mic/audio'),false);});
