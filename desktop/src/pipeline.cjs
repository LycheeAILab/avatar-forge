const fs=require('node:fs/promises'),path=require('node:path');
const {randomUUID,createHash}=require('node:crypto');
const {openAsBlob}=require('node:fs');
const mime=file=>({'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.mp4':'video/mp4','.mov':'video/quicktime','.wav':'audio/wav','.mp3':'audio/mpeg'})[path.extname(file).toLowerCase()];
const idPattern=/^[a-zA-Z0-9_-]{1,100}$/;
class Pipeline{
 constructor({client,root,driver,notify,interval=5000,download,driverHash='73c9cc8dde3ee0f4fe0d39b3720bbc4453ab22b3ede2a9068183d0e1c55d3d0b'}){Object.assign(this,{client,root,driver,notify,interval,driverHash});this.running=false;this.stopped=false;this.download=download||this.fetchMedia.bind(this)}
 dir(user,id){if(!idPattern.test(user)||!idPattern.test(id))throw Error('任务标识无效');return path.join(this.root,user,id)}
 async save(s){const file=path.join(this.dir(s.userId,s.id),'state.json');await fs.writeFile(file+'.tmp',JSON.stringify(s));await fs.rename(file+'.tmp',file);this.notify(this.public(s))}
 public(s){return {id:s.id,title:s.script?.slice(0,40)||'数字人口播',status:s.status,stage:s.stage,createdAt:s.createdAt,error:s.error||null,libraryWarning:s.libraryWarning||null,completed:s.status==='completed'}}
 async list(user){const dir=this.dir(user,'_');const parent=path.dirname(dir);const entries=await fs.readdir(parent).catch(()=>[]);const items=[];for(const id of entries){try{const s=JSON.parse(await fs.readFile(path.join(this.dir(user,id),'state.json'),'utf8'));if(s.userId===user&&s.id===id)items.push(this.public(s))}catch{}}return items.sort((a,b)=>b.createdAt.localeCompare(a.createdAt))}
 async create(user,input){if(this.running)throw Error('已有任务运行中');if(!['image','saved'].includes(input.person)||!['clone','audio','saved'].includes(input.voice)||input.consent!==true)throw Error('请确认素材使用授权');if(input.voice!=='audio'&&(!input.script?.trim()||input.script.length>20000))throw Error('请填写文案（不超过20000字）');
  const model=input.person==='saved'?await this.client.api('/api/avatar-forge/library/model/'+encodeURIComponent(input.modelId)):null;
  const voice=input.voice==='saved'?await this.client.api('/api/avatar-forge/library/voice/'+encodeURIComponent(input.voiceId)):null;
  if(model&&(!model.assetId||!model.playerId)||voice&&!voice.speakerId)throw Error('所选资产尚未就绪');
  const id=randomUUID(),dir=this.dir(user,id);await fs.mkdir(dir,{recursive:true});
  let personFile=null,voiceFile=null;
  if(input.person!=='saved'){personFile=path.join(dir,'person'+path.extname(input.personPath));await fs.copyFile(input.personPath,personFile)}
  if(input.voice!=='saved'){voiceFile=path.join(dir,'voice'+path.extname(input.voicePath));await fs.copyFile(input.voicePath,voiceFile)}
  let coverFile=null;if(input.coverPath){coverFile=path.join(dir,'cover.png');await fs.copyFile(input.coverPath,coverFile)}
  const s={id,userId:user,createdAt:new Date().toISOString(),person:input.person,voice:input.voice,script:input.script||'',personFile,voiceFile,coverFile,modelId:input.modelId,voiceId:input.voiceId,
   clone:model?{assetId:model.assetId}:null,playerId:model?.playerId,voiceClone:voice?{speakerId:voice.speakerId}:null,status:'ready',stage:0};await this.save(s);return s;
 }
 async metadata(s,kind,id,file){const key=kind+'Metadata';if(!id||s[key])return;try{await this.client.api('/api/avatar-forge/library/'+kind+'/'+encodeURIComponent(id),{method:'POST',body:await this.form({name:kind==='model'?'我的模特':'我的音色'},file?{media:file}:{})});s[key]=true;await this.save(s)}catch{s.libraryWarning='资产已保留，封面同步暂未完成';await this.save(s)}}
 async form(fields,files){const form=new FormData();for(const [key,value]of Object.entries(fields))if(value)form.append(key,value);for(const [key,file]of Object.entries(files))form.append(key,await openAsBlob(file,{type:mime(file)}),path.basename(file));return form}
 async submit(s,key,route,options){if(s[key])return s[key];if(s.pending)throw Error('上次提交结果待确认。为避免重复生成，已停止自动重发，请联系管理员核对。');s.pending=key;await this.save(s);const result=await this.client.api('/api/avatar-forge/'+route,options);s[key]=key==='speech'?{id:result.id}:result;s.pending=null;await this.save(s);return result}
 async poll(s,route,digital=false){for(;;){if(this.stopped)throw Error('已暂停等待，可继续查询原任务');let r;try{r=await this.client.api('/api/avatar-forge/'+route)}catch(e){throw Error('查询暂时中断，请继续原任务，不会重复提交。')}const status=digital?r.event_type:r.status;if(['SUCCESS','INFER.SUCCESS'].includes(status))return r;if(['FAILED','FAIL','INFER.FAIL'].includes(status)){s.providerFailed=true;await this.save(s);throw Error('该制作阶段未成功，请联系支持人员核对任务。')}await new Promise(r=>setTimeout(r,this.interval))}}
 async fetchMedia(url,destination){const u=new URL(url);if(u.protocol!=='https:'||u.username||u.password||!(u.hostname.endsWith('.myqcloud.com')||u.hostname.endsWith('.lycheeai.com.cn')))throw Error('媒体下载地址无效');const r=await fetch(u,{redirect:'error',signal:AbortSignal.timeout(600000)});if(!r.ok||!r.body)throw Error('媒体下载失败，请继续原任务');const temp=destination+'.part';const file=await fs.open(temp,'w');let total=0;try{for await(const chunk of r.body){total+=chunk.length;if(total>1024*1024*1024)throw Error('媒体超出下载限制');await file.write(chunk)}}finally{await file.close()}if(total===0)throw Error('媒体为空');if(destination.endsWith('.mp4')){const f=await fs.open(temp,'r');try{const b=Buffer.alloc(12);await f.read(b,0,12,0);if(b.toString('ascii',4,8)!=='ftyp')throw Error('返回结果不是有效MP4')}finally{await f.close()}}await fs.rename(temp,destination)}
 async resume(user,id){if(this.running)throw Error('已有任务运行中');this.running=true;try{return await this.runWithin(user,id)}finally{this.running=false}}
 async runWithin(user,id){const s=JSON.parse(await fs.readFile(path.join(this.dir(user,id),'state.json'),'utf8'));if(s.userId!==user||s.id!==id)throw Error('任务归属无效');if(s.status==='completed')return this.public(s);this.running=true;this.stopped=false;try{
  if(s.providerFailed)throw Error('原任务已明确失败，请核对后新建制作。');if(s.pending)throw Error('提交结果待确认，请联系管理员，不能自动重发。');s.status='processing';s.error=null;s.stage=0;await this.save(s);const dir=this.dir(user,id);let template=s.personFile;
  if(s.person==='image'){
   if(createHash('sha256').update(await fs.readFile(this.driver)).digest('hex')!==this.driverHash)throw Error('内置模板音频校验失败');
   const t=await this.submit(s,'template','template',{method:'POST',body:await this.form({}, {image:s.personFile,audio:this.driver})});
   await this.metadata(s,'model',t.assetId,s.personFile);
   template=path.join(dir,'internal-template.mp4');if(!s.clone){const r=await this.poll(s,'task/'+encodeURIComponent(t.taskId));const media=r.results?.find(x=>x.outputType?.toLowerCase()==='mp4');if(!media?.url)throw Error('模板结果尚不可用');await this.download(media.url,template)}
  }
  if(this.stopped)throw Error('已暂停，可继续原任务');s.stage=1;await this.save(s);let audio=s.voiceFile;
  if(s.voice!=='audio'){
   const v=s.voiceClone||await this.submit(s,'voiceClone','voice/clone',{method:'POST',body:await this.form({}, {voice:s.voiceFile})});const speaker=v.speakerId||v.requestId;if(!speaker)throw Error('声音克隆缺少标识');
   if(s.voice==='clone')await this.metadata(s,'voice',v.voiceId,s.voiceFile);
   const a=await this.submit(s,'speech','voice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({speakerId:speaker,script:s.script})});audio=path.join(dir,'target.mp3');const media=await this.client.api('/api/avatar-forge/voice-result/'+encodeURIComponent(a.id));await this.download(media.url,audio);
  }
  if(this.stopped)throw Error('已暂停，可继续原任务');s.stage=2;await this.save(s);
  const c=s.clone||await this.submit(s,'clone','avatar/clone',{method:'POST',body:await this.form({assetId:s.template?.assetId},{video:template})});
  if(s.person==='video')await this.metadata(s,'model',c.assetId,s.coverFile);
  if(!s.playerId){const clone=await this.poll(s,'digital-task/'+encodeURIComponent(c.requestId),true);s.playerId=clone.body?.player_id;if(!s.playerId)throw Error('数字人克隆尚未返回可用结果');await this.save(s)}const playerId=s.playerId;if(s.person==='image')await fs.rm(template,{force:true});
  if(this.stopped)throw Error('已暂停，可继续原任务');s.stage=3;await this.save(s);
  const infer=await this.submit(s,'inference','avatar/infer',{method:'POST',body:await this.form({assetId:c.assetId,playerId,audioGenerationId:s.speech?.id},{audio})});const result=await this.poll(s,'digital-task/'+encodeURIComponent(infer.requestId),true);if(!result.body?.data)throw Error('最终视频尚不可用');await this.download(result.body.data,path.join(dir,'final.mp4'));
  s.status='completed';s.stage=4;await this.save(s);if(s.person==='image')await fs.rm(template,{force:true});return this.public(s);
 }catch(error){s.status=s.pending?'uncertain':s.providerFailed?'failed':'paused';s.error=error.message;await this.save(s);return this.public(s)}finally{this.running=false}}
}
module.exports={Pipeline,mime};
