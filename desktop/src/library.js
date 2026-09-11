// Asset library is display metadata; it never exposes internal template videos.
(()=>{
 const api=window.avatarStudio,check=r=>{if(!r.ok)throw Error(r.error);return r.data};
 let data={models:[],voices:[]},revision=0;
 const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text)node.textContent=text;return node};
 const nav=document.querySelector('.af-navigation');
 const section=el('section','af-library');section.id='library';section.hidden=true;
 const heading=el('div','af-heading'),title=el('h1','','模特管理'),refresh=el('button','af-secondary','刷新');heading.append(title,refresh);
 const hint=el('p','af-hint','最近 200 项 · 已克隆资产可重复使用，只修改文案不必重新克隆。');
 const grid=el('div','af-library-grid');section.append(heading,hint,grid);document.querySelector('.af-main').append(section);
 const selectors={};
 for(const [kind,label]of [['person','已有模特'],['voice','已有音色']]){
  const group=document.querySelector(`[data-${kind}]`).parentElement;
  const button=el('button','',label);button.dataset[kind]='saved';button.setAttribute('aria-pressed','false');group.prepend(button);
  const select=el('select','af-library-select');select.setAttribute('aria-label',label);select.hidden=true;group.after(select);selectors[kind]=select;
  button.onclick=()=>{
   if(kind==='person'){setPerson('saved');$('person-route').textContent='复用已克隆的模特，跳过模板制作和数字人克隆。'}
   else{setVoice('saved');$('script-section').hidden=false;$('voice-route').textContent='使用已克隆音色合成新文案，不重复克隆。'}
   sync();void load();
  };
  document.querySelectorAll(`[data-${kind}]`).forEach(b=>b.addEventListener('click',sync));
  select.onchange=()=>{
   const row=(kind==='person'?data.models:data.voices).find(x=>x.id===select.value);
   if(kind==='person'&&row?.coverUrl){$('portrait').src=row.coverUrl;$('portrait').hidden=false;$('empty').hidden=true;$('stage-label').hidden=true}
   if(kind==='voice'&&row?.previewUrl){$('voice-player').src=row.previewUrl;$('voice-player').hidden=false}
  };
 }
 function sync(){for(const kind of ['person','voice']){const saved=document.querySelector(`[data-${kind}].is-selected`)?.dataset[kind]==='saved';selectors[kind].hidden=!saved;$(kind+'-drop').hidden=saved;}}
 $('reset').addEventListener('click',sync);
 let tab='models';
 function show(name){page(name);section.hidden=!['models','voices'].includes(name);if(!section.hidden){tab=name;title.textContent=name==='models'?'模特管理':'音色管理';$('breadcrumb').textContent=title.textContent;void load()}}
 for(const [name,label]of [['models','模特管理'],['voices','音色管理']]){const button=el('button','af-nav',label);button.dataset.page=name;nav.append(button)}
 document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>show(b.dataset.page));
 $('back-studio').onclick=()=>show('studio');
 const labels={template_queued:'模板生成中',template_ready:'已生成模板',clone_queued:'克隆中',ready:'已克隆 · 可使用',completed:'已克隆',queued:'克隆中',processing:'克隆中',failed:'失败'};
 function render(){
  for(const [kind,items]of [['person',data.models],['voice',data.voices]]){const select=selectors[kind],previous=select.value;select.replaceChildren(new Option('请选择已克隆的'+(kind==='person'?'模特':'音色'),''));for(const item of items.filter(x=>x.ready))select.add(new Option(item.name,item.id));select.value=previous}
  grid.replaceChildren();for(const item of data[tab]){
   const card=el('article','af-library-card');
   if(tab==='models'){if(item.coverUrl){const image=el('img','af-library-cover');image.src=item.coverUrl;image.alt=item.name;image.loading='lazy';card.append(image)}else card.append(el('div','af-library-placeholder','暂无原图'))}
   else if(item.previewUrl){const audio=el('audio','af-library-audio');audio.controls=true;audio.preload='none';audio.src=item.previewUrl;card.append(audio)}
   const name=el('input','af-library-name');name.value=item.name;name.maxLength=80;name.setAttribute('aria-label','资产名称');
   const status=el('span','af-library-status',labels[item.status]||'等待处理');
   const actions=el('div','af-library-actions'),use=el('button','af-secondary','使用'),save=el('button','af-text-button','保存名称');use.disabled=!item.ready;
   use.onclick=()=>{if(document.querySelector('.af-form').classList.contains('is-busy'))return toast('请先暂停当前制作，再切换素材');const kind=tab==='models'?'person':'voice';show('studio');document.querySelector(`[data-${kind}="saved"]`).click();selectors[kind].value=item.id;selectors[kind].dispatchEvent(new Event('change'))};
   save.onclick=async()=>{save.disabled=true;try{check(await api.renameAsset({kind:tab==='models'?'model':'voice',id:item.id,name:name.value}));item.name=name.value;toast('名称已保存');render()}catch(e){toast(e.message)}finally{save.disabled=false}};
   const media=el('input');media.type='file';media.hidden=true;media.accept=tab==='models'?'image/png,image/jpeg,image/webp':'audio/wav,audio/mpeg';
   const replace=el('button','af-text-button',tab==='models'?'设置原图封面':'设置参考音频');replace.onclick=()=>media.click();
   media.onchange=async()=>{if(!media.files[0])return;replace.disabled=true;try{const token=check(await api.register(media.files[0])).token;check(await api.renameAsset({kind:tab==='models'?'model':'voice',id:item.id,name:name.value,mediaToken:token}));await load()}catch(e){toast(e.message)}finally{replace.disabled=false}};
   actions.append(use,save);card.append(name,status,actions,replace,media);grid.append(card);
  }
  if(!data[tab].length)grid.append(el('p','af-hint',tab==='models'?'还没有模特。完成一次制作后，模特会自动保留在这里。':'还没有音色。克隆成功后，音色会自动保留在这里。'));
 }
 async function load(){const request=++revision;refresh.disabled=true;try{if(!api?.library)throw Error('请在桌面客户端登录后查看资产');const result=check(await api.library());if(request!==revision)return;data=result;render()}catch(e){if(request===revision){grid.replaceChildren(el('p','af-hint',e.message));toast(e.message)}}finally{if(request===revision)refresh.disabled=false}}
 refresh.onclick=load;
 window.avatarLibrary={selection:()=>({modelId:selectors.person.value,voiceId:selectors.voice.value})};
 window.avatarAuth?.onChange(value=>{if(Object.hasOwn(value,'user')){revision++;data={models:[],voices:[]};render();for(const s of Object.values(selectors))s.value='';if(!value.user){$('portrait').removeAttribute('src');$('portrait').hidden=true;$('voice-player').pause();$('voice-player').removeAttribute('src');$('voice-player').hidden=true}}});
 render();
})();
