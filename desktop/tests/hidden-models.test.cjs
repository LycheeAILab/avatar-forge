const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {HiddenModels}=require('../src/hidden-models.cjs');
test('hidden models persist per account and concurrent updates preserve all ids',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'avatar-hidden-'));
 try{const store=new HiddenModels(root);await Promise.all([store.hide('a','m1'),store.hide('a','m2'),store.hide('b','m3')]);const restored=new HiddenModels(root);assert.deepEqual([...await restored.ids('a')],['m1','m2']);assert.deepEqual([...await restored.ids('b')],['m3']);assert.deepEqual([...await restored.ids('c')],[])}finally{await fs.rm(root,{recursive:true,force:true})}
});
