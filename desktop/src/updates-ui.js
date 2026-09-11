// Same interaction contract as CineSleuth: opening the panel never installs.
if(window.avatarStudio){
 const api=window.avatarStudio,button=document.getElementById('update');
 const panel=document.createElement('section');panel.id='update-panel';panel.className='af-update-panel';panel.hidden=true;
 panel.setAttribute('role','dialog');panel.setAttribute('aria-labelledby','update-heading');
 panel.innerHTML='<div class="af-update-heading"><h2 id="update-heading">软件更新</h2><button type="button" id="close-updates" aria-label="关闭更新面板">×</button></div><p id="update-version"></p><p id="update-status" role="status">正在读取版本…</p><progress id="update-progress" max="100" value="0" hidden aria-label="更新下载进度"></progress><div class="af-update-actions"><button type="button" class="af-secondary" id="check-update">检查更新</button><button type="button" class="af-secondary" id="install-update" hidden>重启安装</button></div><p class="af-update-hint">新版自动下载。结束或暂停当前制作后，可重启安装。</p>';
 document.body.append(panel);
 const get=id=>document.getElementById(id),dot=document.createElement('span');dot.className='af-update-dot';dot.hidden=true;button.append(dot);
 button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-controls',panel.id);button.setAttribute('aria-expanded','false');
 let installing=false;
 const unwrap=r=>{if(!r.ok)throw Error(r.error);return r.data};
 function render(s){
  const percent=Math.max(0,Math.min(100,Math.round(s.percent||0)));
  const text={idle:'自动检查新版本',checking:'正在检查更新…',downloading:`正在下载 ${s.version||'新版本'} · ${percent}%`,ready:`${s.version||'新版本'} 已下载，可以重启安装`,current:'当前已是最新版本',error:s.error||'更新失败，请重试',disabled:'开发预览暂不启用自动更新'}[s.status]||'';
  get('update-version').textContent=`Avatar Forge · ${s.currentVersion||'开发版'}`;
  document.querySelector('.af-version>span').textContent=s.currentVersion||'开发版';
  get('update-status').textContent=text;button.title=text;button.setAttribute('aria-label',`软件更新：${text}`);button.dataset.status=s.status;
  dot.hidden=!['ready','error'].includes(s.status);
  get('check-update').disabled=['checking','downloading','ready','disabled'].includes(s.status);
  get('install-update').hidden=s.status!=='ready';get('update-progress').hidden=s.status!=='downloading';get('update-progress').value=percent;
 }
 function position(){const r=button.getBoundingClientRect();panel.style.left=Math.max(12,Math.min(r.left,innerWidth-344))+'px';panel.style.bottom=Math.max(12,innerHeight-r.top+12)+'px'}
 function close(focus=false){panel.hidden=true;button.setAttribute('aria-expanded','false');if(focus)button.focus()}
 async function perform(fn){try{await fn()}catch(e){get('update-status').textContent=e.message}}
 button.onclick=()=>{if(!panel.hidden){close();return}panel.hidden=false;position();button.setAttribute('aria-expanded','true');get('close-updates').focus();void perform(async()=>render(unwrap(await api.updates())))};
 get('close-updates').onclick=()=>close(true);
 document.addEventListener('pointerdown',e=>{if(!panel.contains(e.target)&&!button.contains(e.target))close()});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden){e.preventDefault();close(true)}});
 window.addEventListener('resize',position);
 get('check-update').onclick=()=>perform(async()=>{get('check-update').disabled=true;try{render(unwrap(await api.checkUpdates()))}catch(e){get('check-update').disabled=false;throw e}});
 get('install-update').onclick=()=>perform(async()=>{if(installing)return;installing=true;get('install-update').disabled=true;try{unwrap(await api.installUpdate())}finally{installing=false;get('install-update').disabled=false}});
 api.onUpdate(render);void perform(async()=>render(unwrap(await api.updates())));
}
