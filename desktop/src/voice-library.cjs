const {mime}=require('./pipeline.cjs');
async function cloneVoice({input,file,identity,client,form}){
 if(input?.consent!==true)throw Error('请确认你拥有参考声音的使用授权');
 if(typeof input.name!=='string'||!input.name.trim()||input.name.trim().length>80)throw Error('请填写音色名称（最多80字）');
 if(!file||!mime(file.path).startsWith('audio/')||file.size>15*1024*1024)throw Error('请选择不超过15MB的参考音频');
 await identity();
 const result=await client.api('/api/avatar-forge/voice/clone',{method:'POST',body:await form({}, {voice:file.path})});
 let warning;
 if(result.voiceId)try{await client.api('/api/avatar-forge/library/voice/'+encodeURIComponent(result.voiceId),{method:'POST',body:await form({name:input.name.trim()},{media:file.path})})}catch{warning='音色已提交，名称或试听同步失败，可在音色管理中补充。'}
 return {...result,warning};
}
module.exports={cloneVoice};
