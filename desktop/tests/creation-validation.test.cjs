const test=require('node:test'),assert=require('node:assert/strict');
const {Pipeline}=require('../src/pipeline.cjs');
for(const [overrides,message] of [[{modelId:''},'请选择已有模特'],[{voiceId:''},'请选择已有音色'],[{voice:'audio'},'请选择已有音色'],[{voice:'clone'},'请选择已有音色'],[{script:''},'请填写口播文案']]){
 test(message+JSON.stringify(overrides),async()=>{
  let requests=0;const engine=new Pipeline({client:{async api(){requests++;throw Error('must not request')}},root:'unused'});
  await assert.rejects(engine.create('u',{person:'saved',voice:'saved',modelId:'m',voiceId:'v',script:'测试',consent:true,...overrides}),{message});assert.equal(requests,0);
 });
}
