function mostrar(id){
  document.querySelectorAll('.panel').forEach(x=>x.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
  window.scrollTo({top:0,behavior:'smooth'});
}
function toggleMenu(){
  const n=document.getElementById('menu');
  n.style.display=n.style.display==='none'?'flex':'flex';
}

function setupCanvas(id){
  const canvas=document.getElementById(id);
  const ctx=canvas.getContext('2d');
  function resize(){
    const ratio=window.devicePixelRatio||1;
    const rect=canvas.getBoundingClientRect();
    canvas.width=rect.width*ratio;
    canvas.height=rect.height*ratio;
    ctx.scale(ratio,ratio);
    ctx.lineWidth=2;
    ctx.lineCap='round';
  }
  resize();
  window.addEventListener('resize',resize);
  let drawing=false;
  function pos(e){
    const r=canvas.getBoundingClientRect();
    const p=e.touches?e.touches[0]:e;
    return {x:p.clientX-r.left,y:p.clientY-r.top};
  }
  function start(e){e.preventDefault();drawing=true;const p=pos(e);ctx.beginPath();ctx.moveTo(p.x,p.y)}
  function move(e){if(!drawing)return;e.preventDefault();const p=pos(e);ctx.lineTo(p.x,p.y);ctx.stroke()}
  function end(){drawing=false}
  canvas.addEventListener('mousedown',start); canvas.addEventListener('mousemove',move); canvas.addEventListener('mouseup',end); canvas.addEventListener('mouseleave',end);
  canvas.addEventListener('touchstart',start,{passive:false}); canvas.addEventListener('touchmove',move,{passive:false}); canvas.addEventListener('touchend',end);
}
setupCanvas('firmaRecibe'); setupCanvas('firmaEntrega');

function limpiar(id){
 const c=document.getElementById(id); const ctx=c.getContext('2d'); ctx.clearRect(0,0,c.width,c.height);
}

function canvasData(id){ return document.getElementById(id).toDataURL('image/png'); }

document.getElementById('actaForm').addEventListener('submit', async (e)=>{
 e.preventDefault();
 const form=e.currentTarget;
 const checks=[...document.querySelectorAll('.checks input:checked')].map(x=>x.value);
 document.getElementById('software_estandar').value=checks.join(', ');
 const fd=new FormData(form);
 fd.set('firma_recibe',canvasData('firmaRecibe'));
 fd.set('firma_entrega',canvasData('firmaEntrega'));
 const r=document.getElementById('resultado');
 r.textContent='Generando acta...';
 try{
   const resp=await fetch('/api/actas',{method:'POST',body:fd});
   const data=await resp.json();
   if(!resp.ok) throw new Error(data.detail||'Error');
   r.className='success';
   r.innerHTML=`<b>Acta ${data.consecutivo} generada.</b><br>${data.email_status}<br><br>
   <a href="${data.pdf}" target="_blank">📥 Descargar / abrir PDF</a>`;
 }catch(err){
   r.className='error';
   r.textContent='Error: '+err.message;
 }
});

async function cargarActas(){
 const r=await fetch('/api/actas');
 const data=await r.json();
 let html='<table><thead><tr><th>Acta</th><th>Fecha</th><th>Recibe</th><th>Activo</th><th>Serial</th><th></th></tr></thead><tbody>';
 data.forEach(x=>{
  html+=`<tr><td>${x.consecutivo}</td><td>${x.fecha}</td><td>${x.nombre_recibe||''}</td><td>${x.codigo_activo||''}</td><td>${x.serial||''}</td><td><a target="_blank" href="/api/actas/${x.consecutivo}/pdf">PDF</a></td></tr>`;
 });
 html+='</tbody></table>';
 document.getElementById('tablaActas').innerHTML=html;
}
