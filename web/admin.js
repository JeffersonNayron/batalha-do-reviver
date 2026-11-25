import {request} from './api-client.js';
import {escapeHtml,alertError,dateLabel,empty} from './ui.js';
let orgs=[],adminEvents=[],adminMcs=[],resetToken='';
const asLocal=(value)=>{
 const d=new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value)?value:value+'-03:00');
 const format=new Intl.DateTimeFormat('sv-SE',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',timeZone:'America/Fortaleza'});
 return format.format(d).replace(' ','T');
};
const input=(name,label,type='text',value='',required=false)=>`<label class="field"><span>${label}</span><input name="${name}" type="${type}" value="${escapeHtml(value)}" ${required?'required':''}></label>`;
const checkbox=(name,label,checked=false)=>`<label class="field check"><input type="checkbox" name="${name}" ${checked?'checked':''}>${label}</label>`;
function eventForm(e={}){return `<form class="admin-form" id="event-editor"><input type="hidden" name="record_id" value="${e.id||''}"><div class="form-grid">${input('title','Nome da edição','text',e.title||'',true)}${input('slug','Identificador / slug','text',e.slug||'',true)}<label class="field"><span>Organização</span><select name="organization_id">${orgs.map(o=>`<option value="${o.id}" ${o.id===e.organization_id?'selected':''}>${escapeHtml(o.name)}</option>`).join('')}</select></label>${input('start_at','Data e hora (São Luís)','datetime-local',e.start_at?asLocal(e.start_at):'',true)}${input('venue','Local','text',e.venue||'',true)}${input('city','Cidade','text',e.city||'São Luís',true)}${input('state','UF','text',e.state||'MA',true)}${input('capacity','Vagas para MCs','number',e.capacity??'')}${input('champion_prize','Premiação campeão (R$)','number',e.champion_prize??'')}${input('runner_up_prize','Premiação vice (R$)','number',e.runner_up_prize??'')}${input('registration','Inscrições','text',e.registration||'')}${input('cover_url','Imagem HTTPS ou /assets/','text',e.cover_url||'')}</div><label class="field"><span>Descrição</span><textarea name="description" rows="4">${escapeHtml(e.description||'')}</textarea></label><div class="check-row">${checkbox('free','Evento gratuito',e.free??true)}${checkbox('published','Publicado',e.published??false)}</div><button type="submit" class="button">Salvar edição ↗</button><div role="status" class="form-message" id="event-message"></div></form>`;}
function mcForm(m={}){return `<form class="admin-form" id="mc-editor"><input type="hidden" name="record_id" value="${m.id||''}"><div class="form-grid">${input('stage_name','Nome artístico','text',m.stage_name||'',true)}${input('slug','Identificador / slug','text',m.slug||'',true)}${input('city','Cidade','text',m.city||'São Luís')}${input('instagram','Instagram (sem @)','text',m.instagram||'')}${input('photo_url','Foto HTTPS ou /assets/','text',m.photo_url||'')}</div><label class="field"><span>Biografia</span><textarea name="bio" rows="4">${escapeHtml(m.bio||'')}</textarea></label>${checkbox('published','Publicar perfil',m.published??false)}<button class="button" type="submit">Salvar MC ↗</button><div role="status" class="form-message" id="mc-message"></div></form>`;}
const tabs=()=>`<div class="admin-tabs"><button data-tab="events" class="selected">Edições</button><button data-tab="mcs">MCs</button><button data-tab="orgs">Organizações</button></div>`;
const shell=(body)=>`<div class="container page admin-page"><div class="page-hero"><span class="eyebrow">ÁREA RESTRITA</span><h1>GESTÃO DO <em>REVIVER.</em></h1><p>Cadastre somente conteúdo autorizado e confirmado.</p></div>${body}</div>`;
export async function renderAdmin(){
 const params=new URLSearchParams(location.search);
 if(params.has('reset')){
  resetToken=params.get('reset');
  history.replaceState(history.state,'','/admin');
 }
 const status=await request('/auth/status');
 if(!status.configured)return shell('<div class="notice">O acesso administrativo está indisponível neste ambiente.</div>');
 if(resetToken)return shell(`<form class="login-card" id="reset-confirm"><h2>Redefinir senha</h2><label class="field"><span>Nova senha (mínimo de 12 caracteres)</span><input type="password" name="password" required minlength="12" maxlength="256" autocomplete="new-password"></label><button class="button full" type="submit">Redefinir senha</button><a data-link href="/admin" id="cancel-reset">Voltar ao acesso</a><div class="form-message" role="status"></div></form>`);
 if(!status.authenticated){
  if(params.get('recuperar')==='1'&&status.recovery)return shell(`<form class="login-card" id="reset-request"><h2>Recuperar senha</h2><label class="field"><span>Usuário ou e-mail</span><input name="username" required maxlength="255" autocomplete="username"></label><button class="button full" type="submit">Enviar link de recuperação</button><a data-link href="/admin">Voltar ao acesso</a><div class="form-message" role="status"></div></form>`);
  return shell(`<form class="login-card" id="login-admin"><h2>Acesso da organização</h2><label class="field"><span>Usuário</span><input name="username" required maxlength="255" autocomplete="username"></label><label class="field"><span>Senha</span><input type="password" name="password" required maxlength="256" autocomplete="current-password"></label><button class="button full" type="submit">Entrar ↗</button>${status.recovery?'<a data-link href="/admin?recuperar=1">Esqueci minha senha</a>':''}<div class="form-message" id="login-message" role="status"></div></form>`);
 }
 [orgs,adminEvents,adminMcs]=await Promise.all([request('/organizations'),request('/admin/events'),request('/admin/mcs')]);return shell(`<div class="admin-header"><span>${adminEvents.length} edições · ${adminMcs.length} MCs · ${orgs.length} organizações</span><button id="logout" class="button button-outline small">Sair</button></div>${tabs()}<div id="admin-panel">${renderEventAdmin()}</div>`);}
function renderEventAdmin(){return `<div class="admin-columns"><section><div class="section-title-row"><h2>EDIÇÕES</h2><button class="button small" id="new-event">Nova edição +</button></div><div class="manage-list">${adminEvents.map(e=>`<button type="button" class="manage-item" data-edit-event="${e.id}"><strong>${escapeHtml(e.title)}</strong><span>${dateLabel(e.start_at)} · ${e.published?'Publicado':'Rascunho'}</span></button>`).join('')||'<p>Nenhuma edição cadastrada.</p>'}</div></section><section class="admin-editor"><h2 id="editor-title">Nova edição</h2>${eventForm()}</section></div>`;}
function renderMcAdmin(){return `<div class="admin-columns"><section><div class="section-title-row"><h2>MCs</h2><button class="button small" id="new-mc">Novo MC +</button></div><div class="manage-list">${adminMcs.map(m=>`<button type="button" class="manage-item" data-edit-mc="${m.id}"><strong>${escapeHtml(m.stage_name)}</strong><span>${m.published?'Publicado':'Rascunho'}</span></button>`).join('')||'<p>Não há MCs cadastrados.</p>'}</div></section><section class="admin-editor"><h2 id="editor-title">Novo MC</h2>${mcForm()}</section></div>`;}
function renderOrgAdmin(){return `<div class="admin-columns"><section><h2>ORGANIZAÇÕES CADASTRADAS</h2><div class="manage-list">${orgs.map(o=>`<div class="manage-item"><strong>${escapeHtml(o.name)}</strong><span>${escapeHtml(o.slug)}</span></div>`).join('')}</div></section><section class="admin-editor"><h2>Adicionar organização</h2><form id="org-form" class="admin-form">${input('name','Nome','text','',true)}${input('slug','Identificador / slug','text','',true)}${input('instagram','Instagram','text')}<label class="field"><span>Descrição</span><textarea name="description"></textarea></label><button class="button" type="submit">Salvar organização</button><div class="form-message" id="org-message" role="status"></div></form></section></div>`;}
const dataFrom=(form)=>{const d=Object.fromEntries(new FormData(form));if(form.id==='event-editor'){
 d.organization_id=Number(d.organization_id);for(let k of ['capacity','champion_prize','runner_up_prize'])d[k]=d[k]===''?null:Number(d[k]);d.free=!!form.elements.free.checked;d.published=!!form.elements.published.checked;d.start_at+='-03:00';
 }if(form.id==='mc-editor')d.published=!!form.elements.published.checked; delete d.record_id;return d;};
async function submit(form,endpoint,id,msg){try{const body=dataFrom(form);const url=id?endpoint+'/'+id:endpoint;await request(url,{method:id?'PUT':'POST',body:JSON.stringify(body)});msg.textContent='Salvo com sucesso.';msg.className='form-message success';setTimeout(()=>location.reload(),550);}catch(e){msg.textContent=e.message;msg.className='form-message error';}}
export function mountAdmin(root,render){controller.abort();controller=new AbortController();
 root.querySelector('#cancel-reset')?.addEventListener('click',()=>{resetToken='';},{signal:controller.signal});
 root.addEventListener('submit',async function onSubmit(e){if(!e.target.matches('#login-admin,#reset-request,#reset-confirm,#event-editor,#mc-editor,#org-form'))return;e.preventDefault();const form=e.target;
 if(form.matches('#login-admin,#reset-request,#reset-confirm')){
  const action=form.id==='login-admin'?'login':form.id;
  const data=Object.fromEntries(new FormData(form));
  if(action==='reset-confirm')data.token=resetToken;
  const message=form.querySelector('[role="status"]');
  const button=form.querySelector('button');
  button.disabled=true;
  try{
   await request('/auth/'+action,{method:'POST',body:JSON.stringify(data)});
   if(action==='reset-request'){message.textContent='Se os dados estiverem cadastrados, você receberá o link de recuperação.';return;}
   resetToken='';
   await render();
   if(action==='reset-confirm')root.querySelector('#login-message').textContent='Senha alterada. Entre com a nova senha.';
  }catch(error){message.textContent=error.message;}
  finally{button.disabled=false;}
  return;
 }
 if(form.id==='org-form')return submit(form,'/admin/organizations',null,root.querySelector('#org-message'));
 if(form.id==='event-editor')return submit(form,'/admin/events',new FormData(form).get('record_id'),root.querySelector('#event-message'));
 if(form.id==='mc-editor')return submit(form,'/admin/mcs',new FormData(form).get('record_id'),root.querySelector('#mc-message'));
 },{signal:controller.signal});
 const buttons=root.querySelectorAll('[data-tab]');buttons.forEach(b=>b.addEventListener('click',()=>{buttons.forEach(x=>x.classList.toggle('selected',x===b));const tab=b.dataset.tab;root.querySelector('#admin-panel').innerHTML=tab==='events'?renderEventAdmin():tab==='mcs'?renderMcAdmin():renderOrgAdmin();},{signal:controller.signal}));
 root.addEventListener('click',async e=>{if(e.target.id==='logout'){await request('/auth/logout',{method:'POST'});location.reload();}const evt=e.target.closest('[data-edit-event]');if(evt){const v=adminEvents.find(x=>x.id===Number(evt.dataset.editEvent));root.querySelector('.admin-editor').innerHTML=`<h2>Editar edição</h2>${eventForm(v)}`;}const mc=e.target.closest('[data-edit-mc]');if(mc){const v=adminMcs.find(x=>x.id===Number(mc.dataset.editMc));root.querySelector('.admin-editor').innerHTML=`<h2>Editar MC</h2>${mcForm(v)}`;}if(e.target.id==='new-event')root.querySelector('.admin-editor').innerHTML=`<h2>Nova edição</h2>${eventForm()}`;if(e.target.id==='new-mc')root.querySelector('.admin-editor').innerHTML=`<h2>Novo MC</h2>${mcForm()}`;},{signal:controller.signal});}
let controller=new AbortController();
