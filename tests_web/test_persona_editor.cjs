const {test,afterEach}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
if(!process.env.STAGE_HTML)throw Error('Set STAGE_HTML to the installed stage/index.html path.');
const html=fs.readFileSync(process.env.STAGE_HTML,'utf8');
const code=html.split('/* PERSONA_EDITOR_BEGIN */')[1].split('/* PERSONA_EDITOR_END */')[0];
const Editor=vm.runInNewContext(code+'; PersonaPromptEditor',{setTimeout,clearTimeout});
const editors=[];
function make({storage=new Map(),persist=async()=>{},delay=60000}={}){
  const state={rendered:null,status:null};
  const store={getItem:k=>storage.has(k)?storage.get(k):null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)};
  const e=new Editor({persist,delay,storage:store,render:v=>state.rendered=v,status:(v,bad)=>state.status={v,bad}});
  editors.push(e);
  return {e,state,storage};
}
function load(e,text='原人设',id=''){return e.load({id,name:id || '全局'},text,e.beginLoad());}
afterEach(()=>{for(const e of editors)clearTimeout(e.timer);editors.length=0;});

test('typing automatically persists only the new prompt',async()=>{
  const calls=[];
  const {e,state,storage}=make({persist:async(meta,text)=>calls.push({id:meta.id,text}),delay:5});
  load(e);e.input('新的人设');
  await new Promise(r=>setTimeout(r,20));
  assert.deepEqual(calls,[{id:'',text:'新的人设'}]);
  assert.equal(e.dirty,false);assert.equal(storage.size,0);assert.match(state.status.v,/已保存/);
});
test('closing and reopening cannot replace unsaved typing with an old response',async()=>{
  const {e,state}=make();load(e);const pending=e.beginLoad();e.input('正在编辑');
  assert.equal(e.load({id:''},'旧读取',pending),false);
  assert.equal(e.text,'正在编辑');assert.notEqual(state.rendered,'旧读取');
});
test('response started before a save cannot restore the old saved prompt',async()=>{
  const {e}=make();load(e);e.input('已保存的新内容');const token=e.beginLoad();await e.save();
  assert.equal(e.load({id:''},'原人设',token),false);assert.equal(e.text,'已保存的新内容');
});
test('edits made while saving are written after the earlier request',async()=>{
  let release;const calls=[];
  const {e}=make({persist:async(_,text)=>{calls.push(text);if(calls.length===1)await new Promise(r=>release=r);}});
  load(e);e.input('第一稿');const pending=e.save();e.input('第二稿');release();await pending;
  assert.deepEqual(calls,['第一稿','第二稿']);assert.equal(e.dirty,false);
});
test('reverting to the original text while another save is pending still persists the revert',async()=>{
  let release;const calls=[];
  const {e,storage}=make({persist:async(_,text)=>{calls.push(text);if(calls.length===1)await new Promise(r=>release=r);}});
  load(e);e.input('改稿');const pending=e.save();e.input('原人设');
  assert.equal(storage.get(e.key()),'原人设');release();await pending;
  assert.deepEqual(calls,['改稿','原人设']);
});
test('network failure keeps a reloadable draft and retry saves it',async()=>{
  const storage=new Map();const {e,state}=make({storage,persist:async()=>{throw Error('offline');}});
  load(e);e.input('不能丢的草稿');await assert.rejects(e.save(),/offline/);
  assert.equal(state.status.bad,true);assert.equal(storage.get(e.key()),'不能丢的草稿');
  const writes=[];const next=make({storage,persist:async(_,text)=>writes.push(text)}).e;
  load(next);assert.equal(next.text,'不能丢的草稿');await next.save();assert.deepEqual(writes,['不能丢的草稿']);
});
test('active persona edits retain the loaded persona rather than another selected option',async()=>{
  const calls=[];const {e}=make({persist:async(meta,text)=>calls.push({id:meta.id,text})});
  load(e,'小雅人设','xiaoya');e.input('新的小雅');
  assert.equal(e.load({id:'other'},'别的人设',e.beginLoad()),false);
  await e.save();assert.deepEqual(calls,[{id:'xiaoya',text:'新的小雅'}]);
});
test('older overlapping loads cannot overwrite the latest persona',()=>{
  const {e}=make();const older=e.beginLoad();const newer=e.beginLoad();
  assert.equal(e.load({id:'new'},'新的人设',newer),true);
  assert.equal(e.load({id:'old'},'旧的人设',older),false);assert.equal(e.meta.id,'new');
});
test('empty editing does not erase the saved persona',async()=>{
  const calls=[];const {e,storage}=make({persist:async(_,text)=>calls.push(text)});load(e);e.input('');
  await assert.rejects(e.save(),/不能为空/);assert.deepEqual(calls,[]);assert.equal(storage.get(e.key()),'');
});
