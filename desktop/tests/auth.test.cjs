const test=require('node:test');const assert=require('node:assert/strict');
const {beginLogin,acceptCallback,labOrigin,REDIRECT}=require('../src/auth.cjs');
const {LabClient}=require('../src/lab-client.cjs');
test('PKCE callback is bound to state, exact redirect and expiry',()=>{
  const pending=beginLogin('https://lab.lycheeai.com.cn','test'),code='a'.repeat(43);
  const value=REDIRECT+'?code='+code+'&state='+pending.state;
  assert.equal(acceptCallback(value,pending).codeVerifier,pending.verifier);
  for(const invalid of [value.replace(pending.state,'wrong'),value.replace('/oauth/','//evil/oauth/'),value+'&code='+code,value+'#fragment'])assert.throws(()=>acceptCallback(invalid,pending));
  assert.throws(()=>acceptCallback(value,{...pending,expiresAt:0}));assert.throws(()=>acceptCallback(value,null));
  assert.equal(labOrigin('http://127.0.0.1:3456',false),'http://127.0.0.1:3456');
  assert.throws(()=>labOrigin('http://127.0.0.1:3456',true));assert.throws(()=>labOrigin('https://evil.test',false));
});
test('concurrent API requests refresh once and persist rotated token before use',async()=>{
  let exchanges=0,saved=null;
  const tokens={accessToken:'old',refreshToken:'refresh-old',expiresAt:0};
  const client=new LabClient('http://test',{read:async()=>tokens,write:async t=>{saved=t;},clear:async()=>{}},async(url,options)=>{
    if(url.endsWith('/token')){exchanges++;await new Promise(r=>setTimeout(r,10));return Response.json({accessToken:'new',refreshToken:'refresh-new',expiresIn:600});}
    assert.equal(options.headers.Authorization,'Bearer new');assert.equal(saved.refreshToken,'refresh-new');return Response.json({ok:true});
  });
  await client.initialize();await Promise.all([client.api('/api/one'),client.api('/api/two')]);assert.equal(exchanges,1);
});
test('refresh rejection clears credentials, network failure retains them for retry',async()=>{
  for(const status of [401,503]){let cleared=false;const client=new LabClient('http://test',{read:async()=>({refreshToken:'old',expiresAt:0}),write:async()=>{},clear:async()=>{cleared=true;}},async()=>Response.json({message:'failed'},{status}));
    await client.initialize();await assert.rejects(client.api('/api/test'));assert.equal(cleared,status===401);}
});
