if(window.avatarStudio){
 const api=window.avatarStudio;
 let updateState={status:'idle'};
 const updateButton=document.getElementById('update');
 function displayUpdate(state){updateState=state;updateButton.title=({idle:'检查更新',checking:'正在检查',downloading:'正在下载 '+(state.percent||0)+'%',ready:'更新已下载，点击安装',current:'当前已是最新版本',error:'更新失败，点击重试',disabled:'测试版暂不启用自动更新'})[state.status];document.querySelector('.af-version>span').textContent=state.currentVersion||'开发版'}
 api.onUpdate(displayUpdate);api.updates().then(r=>{if(r.ok)displayUpdate(r.data)});
 updateButton.onclick=async()=>{try{if(updateState.status==='ready'){if(confirm('重启并安装更新？'))check(await api.installUpdate())}else{displayUpdate(check(await api.checkUpdates()));message(updateButton.title)}}catch(e){message(e.message)}};
 let personToken=null,voiceToken=null,active=null;
 document.querySelector('.af-preview-tag').textContent='Lab 云端制作';
 document.querySelector('.af-local-note').textContent='Avatar Forge · Windows';
 document.querySelector('.af-action-note').textContent='素材将用于 Lab 云端制作，请确认你拥有使用授权。';
 const button=document.getElementById('simulate');button.textContent='生成数字人口播视频';
 const exportButton=document.createElement('button');exportButton.className='af-secondary';exportButton.textContent='下载最终视频';exportButton.hidden=true;document.querySelector('.af-preview-panel').append(exportButton);
 const pause=document.createElement('button');pause.className='af-text-button';pause.textContent='暂停等待';pause.hidden=true;document.querySelector('.af-progress-panel').append(pause);
 const check=result=>{if(!result.ok)throw Error(result.error);return result.data};
 function message(text){const t=document.getElementById('toast');t.textContent=text;t.hidden=false;setTimeout(()=>t.hidden=true,6000)}
 for(const kind of ['person','voice']){
  let revision=0;
  async function register(file){const current=++revision;if(kind==='person')personToken=null;else voiceToken=null;if(!file)return;try{const data=check(await api.register(file));if(current!==revision)return;if(kind==='person')personToken=data.token;else voiceToken=data.token}catch(e){message(e.message)}}
  document.getElementById(kind+'-file').addEventListener('change',e=>register(e.target.files[0]));
  document.getElementById(kind+'-drop').addEventListener('drop',e=>register(e.dataTransfer.files[0]));
  document.querySelectorAll(`[data-${kind}]`).forEach(b=>b.addEventListener('click',()=>{revision++;if(kind==='person')personToken=null;else voiceToken=null}));
 }
 function show(task){active=task;document.querySelector('.af-form').classList.toggle('is-busy',task.status==='processing');document.querySelector('.af-form').inert=task.status==='processing';button.disabled=task.status==='processing';pause.hidden=task.status!=='processing';document.getElementById('progress-status').textContent=({processing:'正在制作',completed:'已完成',paused:'已暂停，可继续',failed:'制作失败',uncertain:'提交结果待确认'})[task.status]||'准备中';
  document.querySelectorAll('#progress li').forEach((el,i)=>{el.className=i<task.stage?'is-done':i===task.stage?'is-current':'';el.querySelector('small').textContent=i<task.stage?'已完成':i===task.stage?'处理中':'等待';});
  document.getElementById('result').hidden=true;exportButton.hidden=!task.completed;
  if(task.completed){const video=document.getElementById('person-player');document.getElementById('empty').hidden=true;document.getElementById('portrait').hidden=true;video.hidden=false;video.src='avatar-media://result/'+task.id;document.getElementById('stage-label').textContent='最终数字人口播视频';document.getElementById('stage-label').hidden=false;document.getElementById('preview-state').textContent='制作完成'}
  if(task.error)message(task.error);else if(task.completed&&task.libraryWarning)message(task.libraryWarning);
 }
 api.onChange(show);
 button.onclick=async()=>{button.disabled=true;try{const selection=window.avatarLibrary?.selection()||{};let cover;
  if(document.querySelector('[data-person].is-selected').dataset.person==='saved'&&!selection.modelId)throw Error('请选择已有模特');
  if(!selection.voiceId)throw Error('请选择已有音色');
  if(!document.getElementById('script').value.trim())throw Error('请填写口播文案');
  if(!document.getElementById('consent').checked)throw Error('请确认素材使用授权');
  if(document.querySelector('[data-person].is-selected').dataset.person==='video'&&personUrl){const v=document.createElement('video');v.preload='auto';v.muted=true;try{await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error('读取原视频首帧超时，请检查视频')),15000);v.onloadeddata=()=>{clearTimeout(timeout);resolve()};v.onerror=()=>{clearTimeout(timeout);reject(Error('原视频无法读取'))};v.src=personUrl});const canvas=document.createElement('canvas');canvas.width=480;canvas.height=Math.min(1920,Math.round(480*v.videoHeight/v.videoWidth));canvas.getContext('2d').drawImage(v,0,0,canvas.width,canvas.height);cover=canvas.toDataURL('image/png')}finally{v.removeAttribute('src');v.load()}}
  const data=check(await api.create({personToken,voiceToken,person:document.querySelector('[data-person].is-selected').dataset.person,voice:document.querySelector('[data-voice].is-selected').dataset.voice,script:document.getElementById('script').value,consent:document.getElementById('consent').checked,...selection,cover}));show(data)}catch(e){message(e.message)}finally{if(active?.status!=='processing')button.disabled=false}};
 pause.onclick=async()=>{try{message(check(await api.pause()).message)}catch(e){message(e.message)}};
 exportButton.onclick=async()=>{if(!active)return;try{const result=check(await api.export(active.id));if(result.saved)message('视频已保存')}catch(e){message(e.message)}};
 async function history(){const panel=document.querySelector('.af-history-empty');panel.replaceChildren();const state=document.createElement('p');state.textContent='正在读取制作历史…';panel.append(state);try{const data=check(await api.history());panel.replaceChildren();if(!data.items.length&&!data.cloud.length){state.textContent='还没有制作记录';panel.append(state)}
  for(const item of data.items){const row=document.createElement('div');row.className='af-history-row';const text=document.createElement('div');const title=document.createElement('strong');title.textContent=item.title;const detail=document.createElement('p');detail.textContent=new Date(item.createdAt).toLocaleString()+' · '+({completed:'已完成',paused:'已暂停',processing:'处理中',uncertain:'待核对',failed:'失败',ready:'待开始'})[item.status];text.append(title,detail);const action=document.createElement('button');action.className='af-secondary';action.textContent=item.completed?'查看视频':'继续查询';action.disabled=['failed','uncertain'].includes(item.status);action.onclick=async()=>{document.getElementById('back-studio')?.click();document.querySelector('[data-page="studio"]').click();if(item.completed)show(item);else try{check(await api.resume(item.id))}catch(e){message(e.message)}};row.append(text,action);panel.append(row)}
  if(data.cloud.length){const title=document.createElement('h2');title.textContent='云端成片';const grid=document.createElement('div');grid.className='af-cloud-grid';panel.append(title,grid);for(const item of data.cloud){if(!item.url)continue;const video=document.createElement('video');video.controls=true;video.preload='metadata';video.src=item.url;video.className='af-cloud-video';grid.append(video)}}
 }catch(e){state.textContent=e.message;panel.replaceChildren(state)}}
 document.querySelector('[data-page="history"]').addEventListener('click',history);
 window.avatarAuth.onChange(value=>{if(Object.hasOwn(value,'user')&&!value.user){document.getElementById('person-player').pause();document.getElementById('person-player').removeAttribute('src');exportButton.hidden=true;active=null;document.querySelector('.af-history-empty').replaceChildren();}});
}
