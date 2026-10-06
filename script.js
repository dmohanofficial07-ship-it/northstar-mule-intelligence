const sidebar=document.querySelector('.sidebar');
document.querySelector('.menu').onclick=()=>sidebar.classList.toggle('open');
document.querySelectorAll('.sidebar nav a').forEach(a=>a.onclick=()=>{document.querySelectorAll('.sidebar nav a').forEach(x=>x.classList.remove('active'));a.classList.add('active');sidebar.classList.remove('open')});

const detail={type:document.querySelector('#detail-type'),score:document.querySelector('#detail-score'),name:document.querySelector('#detail-name'),id:document.querySelector('#detail-id'),summary:document.querySelector('#detail-summary'),signal:document.querySelector('#detail-signal'),value:document.querySelector('#detail-value')};
document.querySelectorAll('.entity-node').forEach(node=>node.addEventListener('click',()=>{
  document.querySelectorAll('.entity-node').forEach(item=>item.classList.toggle('active',item===node));
  detail.type.textContent=node.dataset.type;detail.score.textContent=`${node.dataset.score} risk`;detail.name.textContent=node.dataset.name;detail.id.textContent=node.dataset.id;detail.summary.textContent=node.dataset.summary;detail.signal.textContent=node.dataset.signal;detail.value.textContent=node.dataset.value;
}));

const traceButton=document.querySelector('#trace-funds'),networkCanvas=document.querySelector('.network-canvas'),traceStatus=document.querySelector('#trace-status');
traceButton.addEventListener('click',()=>{
  networkCanvas.classList.remove('tracing');void networkCanvas.offsetWidth;networkCanvas.classList.add('tracing');traceButton.disabled=true;traceButton.textContent='Tracing…';traceStatus.textContent='Following ₹5.94L to Orion Exports';
  setTimeout(()=>{traceButton.disabled=false;traceButton.textContent='Trace again';traceStatus.textContent='Path completed in 18 minutes · 7 linked entities'},2200);
});

const rows=[...document.querySelectorAll('tbody tr')],search=document.querySelector('#search'),chips=document.querySelector('#chips'),empty=document.querySelector('#empty');let risk='all';
document.querySelector('#filter').onclick=()=>chips.hidden=!chips.hidden;
function filter(){const q=search.value.toLowerCase();let visible=0;rows.forEach(row=>{row.hidden=!((risk==='all'||row.dataset.risk===risk)&&row.textContent.toLowerCase().includes(q));if(!row.hidden)visible++});empty.hidden=visible>0}
search.oninput=filter;chips.querySelectorAll('button').forEach(b=>b.onclick=()=>{risk=b.dataset.risk;chips.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));filter()});

const dialog=document.querySelector('#case'),content=document.querySelector('#case-content'),toast=document.querySelector('#toast');
document.querySelectorAll('.review').forEach(button=>button.onclick=()=>{const td=button.closest('tr').children;const txn=td[0].querySelector('b').textContent,customer=td[1].querySelector('b').textContent,customerId=td[1].querySelector('small').textContent,amount=td[2].querySelector('b').textContent,score=td[3].querySelector('mark').textContent,signal=td[4].querySelector('b').textContent,channel=td[5].textContent;content.innerHTML=`<h2>${txn}</h2><p class="case-meta">${customer} · ${customerId}</p><div class="case-amount">${amount}</div><div class="facts"><div><span>Risk score</span><b>${score} / 100</b></div><div><span>Primary signal</span><b>${signal}</b></div><div><span>Payment route</span><b>${td[0].querySelector('small').textContent}</b></div><div><span>Channel</span><b>${channel}</b></div></div>`;dialog.dataset.txn=txn;dialog.showModal()});
dialog.querySelector('.close').onclick=()=>dialog.close();dialog.onclose=()=>{if(!['safe','blocked'].includes(dialog.returnValue))return;toast.textContent=`${dialog.dataset.txn} ${dialog.returnValue==='safe'?'marked as safe':'blocked and escalated'}. Audit event recorded.`;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),3000)};

const nf=new Intl.NumberFormat('en-IN');document.querySelectorAll('[data-count]').forEach(el=>{const n=+el.dataset.count,start=performance.now();function tick(now){const p=Math.min((now-start)/700,1);el.textContent=nf.format(Math.floor(n*(1-(1-p)**3)));if(p<1)requestAnimationFrame(tick)}requestAnimationFrame(tick)});
