/**
 * Omnia Deployment Flow Interactive Chart
 */
(function(){
  const S = { mode:'standard', ome:'no', aarch64:'no' };
  let prevKeys = new Set();
  let isFirst = true;
  let modeClicked = false;
  let animating = false;

  window._ofs = function(k,v){
    if(animating) return;
    if(k==='mode') modeClicked = true;
    S[k]=v;

    // instantly reflect button state
    if(k==='mode'){
      document.querySelectorAll('.of-m button').forEach(b=>b.className='');
      const btns=document.querySelectorAll('.of-m button');
      if(btns[0]) btns[0].className=v==='standard'?'a st':'';
      if(btns[1]) btns[1].className=v==='buildstream'?'a bs':'';
    } else {
      const dec=document.querySelector(`[data-okey="d-${k==='ome'?'ome':'arch-'+S.mode[0]}"] .of-do`);
      if(dec) dec.querySelectorAll('.of-b').forEach(b=>{
        b.classList.toggle('a', b.textContent.trim().toLowerCase()===(v==='yes'?'yes':'no'));
      });
    }

  const oldKeys = new Set(prevKeys);

    const newParts = buildParts();
    const newKeys = new Set(newParts.map(p=>p.key));
    const exiting = [...prevKeys].filter(k=>!newKeys.has(k));

    if(exiting.length > 0){
      animating = true;
      const els = document.querySelectorAll('[data-okey]');
      let count = 0;
      let done = 0;

      els.forEach(el=>{
        if(exiting.includes(el.getAttribute('data-okey'))){
          count++;
          el.classList.add('of-exit');
          el.addEventListener('animationend',()=>{
            done++;
            if(done>=count){ animating=false; doRender(newParts,newKeys); }
          },{once:true});
        }
      });

      setTimeout(()=>{ if(done<count){ animating=false; doRender(newParts,newKeys); } }, 500);
    } else {
      doRender(newParts,newKeys);
    }
  };

  function buildParts(){
    const parts = [];

    function add(key,html){ parts.push({key,html}); }
    function pill(key,t,c){ add(key,`<div class="of-pill ${c}">${t}</div>`); }
    function cn(key,c=''){ add(key,`<div class="of-c ${c}"></div>`); }
    function st(key,t,d,c=''){ add(key,`<div class="of-s ${c}"><div class="t">${t}</div>${d?`<div class="d">${d}</div>`:''}</div>`); }
    function dec(key,l,opts,stateKey){
      const bs=opts.map(o=>{
        const a=S[stateKey]===o.v?'a':'';
        return `<button class="of-b ${a}" onclick="_ofs('${stateKey}','${o.v}')">${o.l}</button>`;
      }).join('');
      add(key,`<div class="of-d"><div class="of-dl">${l}</div><div class="of-do">${bs}</div></div>`);
    }
    function md(key){
      const sc=S.mode==='standard'?'a st':'';
      const bc=S.mode==='buildstream'?'a bs':'';
      const p=!modeClicked?'pulse':'';
      let html=`<div style="display:flex;flex-direction:column;align-items:center;width:100%">`;
      html+=`<div class="of-m ${p}"><button class="${sc}" onclick="_ofs('mode','standard')">Standard</button><button class="${bc}" onclick="_ofs('mode','buildstream')">BuildStream</button></div>`;
      if(!modeClicked) html+=`<div class="of-hint">↑ Click to switch deployment method</div>`;
      html+=`</div>`;
      add(key,html);
    }
    function dv(key,t){ add(key,`<div class="of-dv"><span>${t}</span></div>`); }

    pill('start','Start','s');
    cn('c0');
    dv('dv-m','Deployment Method');
    cn('c0a','sm na');
    md('mode');
    cn('c0b');

    st('s-build','Build Omnia Images','<code>omnia-artifactory</code> repo');
    cn('c1');
    st('s-create','Create Omnia Core Container','<code>omnia.sh</code>');
    cn('c2');
    st('s-login','Log in to Core Container','<code>ssh omnia_core</code>');
    cn('c3');
    st('s-input','Update Input Files','<code>/opt/omnia/input/project_default</code>');
    cn('c4');

    dec('d-ome','Discover nodes using OME?',[
     {l:'Yes',v:'yes'}, {l:'No',v:'no'}
    ],'ome');
    cn('c5');

    if(S.ome==='yes'){
      st('s-ome-y','Generate PXE Mapping File via OME','<code>discovery.yml</code>');
    } else {
      st('s-ome-n','Create PXE Mapping File Manually','<code>&lt;pxe_mapping_file_path.csv&gt;</code>');
    }
    cn('c6');

    if(S.mode==='standard'){
      st('ss-oim','Deploy Containers on OIM','<code>prepare_oim.yml</code>');
      cn('cs1');
      st('ss-pulp','Download Packages to Pulp Repo','<code>local_repo.yml</code>');
      cn('cs2');
      st('ss-img','Build x86_64 Diskless Images','<code>build_image_x86_64.yml</code>');
      cn('cs3');

      dec('d-arch-s','aarch64 required?',[
        {l:'Yes',v:'yes'}, {l:'No',v:'no'}
      ],'aarch64');
      cn('cs4');

      if(S.aarch64==='yes'){
        st('ss-rhel','Install RHEL10 on aarch64 Node','');
        cn('cs5');
        st('ss-abuild','Build aarch64 Diskless Images','<code>build_image_aarch64.yml</code>');
        cn('cs6');
      }

      st('ss-prov','Provision Nodes','<code>provision.yml</code>');
      cn('cs7');
      st('ss-pxe','PXE Boot Nodes','<code>set_pxe_boot.yml</code>');
    }

    if(S.mode==='buildstream'){
      
      dec('d-arch-b','aarch64 Required?',[
        {l:'Yes',v:'yes'}, {l:'No',v:'no'}
      ],'aarch64');
      cn('cb1');

      if(S.aarch64==='yes'){
        st('sb-rhel','Install RHEL10 on aarch64 Node','','bsm');
        cn('cb2');
      }

      st('sb-oim','Deploy BuildStreaM on OIM','<code>prepare_oim.yml</code>','bsm');
      cn('cb3');
      st('sb-git','Deploy GitLab','<code>gitlab.yml</code>','bsm');
      cn('cb4');
      st('sb-cat','Update Catalog','GitLab','bsm');
      cn('cb5');
      st('sb-ci','Triggers Build Pipeline','GitLab','bsm');
      cn('cb6');
      st('sb-pxe','Modify PXE Mapping File','GitLab','bsm');
      cn('cb7');
      st('sb-dep','Triggers Deploy Pipeline','GitLab','bsm');
    }

    cn('cf0');
    dv('dv-fin','Your cluster is now ready');
    cn('cf1','sm na');
    st('s-telem','Enable Telemetry','<code>telemetry.yml</code>');
    cn('cf2');
    pill('end','End','e');

    return parts;
  }

  function doRender(parts, newKeys){
    let delay = 0;

    const html = parts.map(p=>{
      const brandNew = !isFirst && !prevKeys.has(p.key);
      if(brandNew){
        const d = delay * 0.08;
        delay++;
        return `<div data-okey="${p.key}" class="of-new" style="animation-delay:${d}s">${p.html}</div>`;
      }
      return `<div data-okey="${p.key}">${p.html}</div>`;
    }).join('');

    prevKeys = newKeys;
    isFirst = false;

    document.getElementById('omniaDeploymentFlowchart').innerHTML = html;
  }

  // initial render
  const initParts = buildParts();
  const initKeys = new Set(initParts.map(p=>p.key));
  doRender(initParts, initKeys);
})();
