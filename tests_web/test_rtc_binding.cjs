const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
if(!process.env.STAGE_HTML)throw Error('Set STAGE_HTML to stage/index.html');
const html=fs.readFileSync(process.env.STAGE_HTML,'utf8');
const code=html.split('/* RTC_VIDEO_BINDING_BEGIN */')[1].split('/* RTC_VIDEO_BINDING_END */')[0];
const create=vm.runInNewContext(code+';createRtcVideoBinding',{console});
function fixture(){const calls=[];const video={};let active=true;const b=create({setRemoteViewConfig:(...x)=>calls.push(x)},video,()=>{},()=>active);return {b,calls,video,stale:()=>active=false};}
test('subscribing does not repeatedly reset the player',()=>{const {b,calls}=fixture();b.update('u',1,0);b.update('u',1,2);assert.equal(calls.length,0);});
test('camera is attached only once even after duplicate subscribed events',()=>{const {b,calls,video}=fixture();b.update('u',1,3);b.update('u',1,3);assert.equal(calls.length,1);assert.deepEqual(calls[0],[video,'u',1]);});
test('screen events never overwrite a subscribed camera',()=>{const {b,calls}=fixture();b.update('u',1,3);b.update('u',2,3);assert.equal(calls.length,1);});
test('screen-only publishers can still be displayed',()=>{const {b,calls,video}=fixture();b.update('u',2,3);assert.deepEqual(calls[0],[video,'u',2]);});
test('switching tracks detaches the old track before attaching the new one',()=>{const {b,calls,video}=fixture();b.update('u',2,3);b.update('u',1,3);assert.deepEqual(calls.slice(1),[[null,'u',2],[video,'u',1]]);});
test('camera unsubscription falls back to an available screen',()=>{const {b,calls,video}=fixture();b.update('u',1,3);b.update('u',2,3);b.update('u',1,1);assert.deepEqual(calls.at(-1),[video,'u',2]);});
test('reconnection binds again without stale callbacks from an older engine',()=>{const {b,calls}=fixture();b.update('u',1,3);b.update('u',1,1);b.update('u',1,3);assert.equal(calls.filter(x=>x[0]).length,2);});
test('offline allows the next subscribed event to bind again',()=>{const {b,calls}=fixture();b.update('u',1,3);b.offline('u');b.update('u',1,3);assert.equal(calls.length,2);});
test('old engine callbacks cannot touch the new player',()=>{const {b,calls,stale}=fixture();stale();b.update('u',1,3);assert.equal(calls.length,0);});
