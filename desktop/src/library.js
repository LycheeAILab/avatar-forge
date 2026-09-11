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
 const selectors={},pickers={};
 let preview=null;
 function stopPreview(){if(preview){preview.pause();preview=null}document.querySelectorAll('.af-voice-play').forEach(b=>{b.textContent='▶';b.setAttribute('aria-pressed','false')})}
 function playButton(item){const b=el('button','af-voice-play','▶');b.type='button';b.disabled=!item.previewUrl;b.setAttribute('aria-label',item.previewUrl?'试听 '+item.name:'暂无试听音频');b.setAttribute('aria-pressed','false');b.onclick=async()=>{const playing=b.getAttribute('aria-pressed')==='true';stopPreview();if(playing)return;const audio=new Audio(item.previewUrl);preview=audio;b.textContent='Ⅱ';b.setAttribute('aria-pressed','true');audio.onended=()=>{if(preview===audio)stopPreview()};try{await audio.play()}catch{if(preview===audio)stopPreview();toast('试听加载失败，请刷新后重试')}};return b}
 for(const [kind,label]of [['person','已有模特'],['voice','已有音色']]){
  const group=kind==='voice'?document.querySelector('[aria-label="声音用途"]'):document.querySelector(`[data-${kind}]`).parentElement;
  const button=el('button','',label);button.dataset[kind]='saved';button.setAttribute('aria-pressed','false');group.prepend(button);
  const select=el('select','af-library-select');select.setAttribute('aria-label',label);select.hidden=true;group.after(select);selectors[kind]=select;
  const picker=el('div','af-asset-picker');picker.hidden=true;picker.setAttribute('aria-label',label);select.after(picker);pickers[kind]=picker;
  button.onclick=()=>{
   if(kind==='person'){setPerson('saved');$('person-route').textContent='复用已克隆的模特，跳过模板制作和数字人克隆。'}
   else{setVoice('saved');$('script-section').hidden=false;$('voice-route').textContent='使用已克隆音色合成新文案，不重复克隆。'}
   sync();void load();
  };
  document.querySelectorAll(`[data-${kind}]`).forEach(b=>b.addEventListener('click',sync));
  select.onchange=()=>{
   renderChoices(kind);
   const row=(kind==='person'?data.models:data.voices).find(x=>x.id===select.value);
   if(kind==='person'){$('person-player').pause();$('person-player').hidden=true;$('portrait').removeAttribute('src');$('portrait').hidden=true;$('empty').hidden=false;$('stage-label').hidden=true;if(row?.coverUrl){$('portrait').src=row.coverUrl;$('portrait').hidden=false;$('empty').hidden=true}}
   if(kind==='voice'){stopPreview();$('voice-player').pause();$('voice-player').removeAttribute('src');$('voice-player').hidden=true}
  };
 }
 function sync(){stopPreview();for(const kind of ['person','voice']){const saved=document.querySelector(`[data-${kind}].is-selected`)?.dataset[kind]==='saved';selectors[kind].hidden=true;pickers[kind].hidden=!saved;$(kind+'-drop').hidden=saved;}}
 $('reset').addEventListener('click',sync);
 let tab='models';
 function show(name){stopPreview();page(name);section.hidden=!['models','voices'].includes(name);if(!section.hidden){tab=name;title.textContent=name==='models'?'模特管理':'音色管理';$('breadcrumb').textContent=title.textContent;void load()}}
 for(const [name,label]of [['models','模特管理'],['voices','音色管理']]){const button=el('button','af-nav',label);button.dataset.page=name;nav.append(button)}
 document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>show(b.dataset.page));
 $('back-studio').onclick=()=>show('studio');
 const labels={template_queued:'模板生成中',template_ready:'已生成模板',clone_queued:'克隆中',ready:'已克隆 · 可使用',completed:'已克隆',queued:'克隆中',processing:'克隆中',failed:'失败'};
 function renderChoices(kind){
  const picker=pickers[kind];picker.replaceChildren();
  const items=(kind==='person'?data.models:data.voices).filter(x=>x.ready);
  for(const item of items){
   const card=el('div','af-asset-choice'+(kind==='voice'?' af-voice-choice':''));
   const button=el('button','af-asset-select');button.type='button';button.setAttribute('aria-pressed',String(selectors[kind].value===item.id));button.setAttribute('aria-label','选择 '+item.name);
   if(kind==='person'){if(item.coverUrl){const img=el('img');img.src=item.coverUrl;img.alt='';img.loading='lazy';button.append(img)}else button.append(el('span','af-model-missing','暂无封面'))}
   else{card.append(playButton(item));}
   button.append(el('span','af-choice-name',item.name));
   button.onclick=()=>{selectors[kind].value=item.id;selectors[kind].dispatchEvent(new Event('change'))};card.append(button);
   if(kind==='voice')card.append(el('small','af-hint',item.previewUrl?'参考音频试听':'暂无试听音频'));
   picker.append(card);
  }
  if(!items.length)picker.append(el('p','af-hint','暂无已克隆资产，请先上传素材完成制作。'));
 }
 function render(){
  for(const [kind,items]of [['person',data.models],['voice',data.voices]]){const select=selectors[kind],previous=select.value;select.replaceChildren(new Option('请选择已克隆的'+(kind==='person'?'模特':'音色'),''));for(const item of items.filter(x=>x.ready))select.add(new Option(item.name,item.id));select.value=previous}
  for(const kind of ['person','voice'])renderChoices(kind);
  grid.replaceChildren();for(const item of data[tab]){
   const card=el('article','af-library-card');
   if(tab==='models'){if(item.coverUrl){const image=el('img','af-library-cover');image.src=item.coverUrl;image.alt=item.name;image.loading='lazy';card.append(image)}else card.append(el('div','af-library-placeholder','暂无原图'))}
   else {card.classList.add('af-voice-library');card.append(playButton(item));if(!item.previewUrl)card.append(el('small','af-hint','暂无试听音频'))}
   const name=el('input','af-library-name');name.value=item.name;name.maxLength=80;name.setAttribute('aria-label','资产名称');
   const status=el('span','af-library-status',labels[item.status]||'等待处理');
   const actions=el('div','af-library-actions'),use=el('button','af-secondary','使用'),save=el('button','af-text-button','保存名称');use.disabled=!item.ready;
   use.onclick=()=>{if(document.querySelector('.af-form').classList.contains('is-busy'))return toast('请先暂停当前制作，再切换素材');const kind=tab==='models'?'person':'voice';show('studio');document.querySelector(`[data-${kind}="saved"]`).click();selectors[kind].value=item.id;selectors[kind].dispatchEvent(new Event('change'))};
   save.onclick=async()=>{save.disabled=true;try{check(await api.renameAsset({kind:tab==='models'?'model':'voice',id:item.id,name:name.value}));item.name=name.value;toast('名称已保存');render()}catch(e){toast(e.message)}finally{save.disabled=false}};
   const media=el('input');media.type='file';media.hidden=true;media.accept=tab==='models'?'image/png,image/jpeg,image/webp':'audio/wav,audio/mpeg';
   const replace=el('button','af-text-button',tab==='models'?'设置原图封面':'设置参考音频');replace.onclick=()=>media.click();
   media.onchange=async()=>{if(!media.files[0])return;replace.disabled=true;try{const token=check(await api.register(media.files[0])).token;check(await api.renameAsset({kind:tab==='models'?'model':'voice',id:item.id,name:name.value,mediaToken:token}));await load()}catch(e){toast(e.message)}finally{replace.disabled=false}};
   actions.append(use,save);card.append(name,status,actions,replace,media);
   if(tab==='models'){
    const remove=el('button','af-model-delete','删除模特');remove.type='button';
    remove.onclick=async()=>{remove.disabled=true;try{const result=check(await api.hideModel(item.id));if(!result.hidden)return;data.models=data.models.filter(model=>model.id!==item.id);if(selectors.person.value===item.id){selectors.person.value='';selectors.person.dispatchEvent(new Event('change'))}render();toast('模特已从列表移除')}catch(e){toast(e.message)}finally{remove.disabled=false}};
    card.append(remove);
   }
   grid.append(card);
  }
  if(!data[tab].length)grid.append(el('p','af-hint',tab==='models'?'还没有模特。完成一次制作后，模特会自动保留在这里。':'还没有音色。克隆成功后，音色会自动保留在这里。'));
 }
 async function load(){const request=++revision;refresh.disabled=true;try{if(!api?.library)throw Error('请在桌面客户端登录后查看资产');const result=check(await api.library());if(request!==revision)return;data=result;render()}catch(e){if(request===revision){grid.replaceChildren(el('p','af-hint',e.message));for(const picker of Object.values(pickers))picker.replaceChildren(el('p','af-hint',e.message));toast(e.message)}}finally{if(request===revision)refresh.disabled=false}}
 refresh.onclick=load;
 window.avatarLibrary={selection:()=>({modelId:selectors.person.value,voiceId:selectors.voice.value})};
 window.avatarAuth?.onChange(value=>{if(Object.hasOwn(value,'user')){revision++;data={models:[],voices:[]};render();for(const s of Object.values(selectors))s.value='';if(!value.user){$('portrait').removeAttribute('src');$('portrait').hidden=true;$('voice-player').pause();$('voice-player').removeAttribute('src');$('voice-player').hidden=true}}});
 setVoice('saved');sync();
 render();
 window.avatarAuth?.onChange(()=>stopPreview());
 window.addEventListener('beforeunload',stopPreview);
})();
