/**
 * Omnia Deployment Flow Interactive Chart
 */
(function(){
  const flowContainer = document.getElementById('omniaDeploymentFlowchart');
  if (!flowContainer) return;

  const S = { mode: 'standard', ome: 'no', aarch64: 'no' };
  let prevKeys = new Set();
  let isFirst = true;
  let modeClicked = false;
  let animating = false;

  function updateControls(k, v) {
    if (k === 'mode') {
      const buttons = flowContainer.querySelectorAll('.of-m button');
      buttons.forEach((btn, idx) => {
        const mode = idx === 0 ? 'standard' : 'buildstream';
        btn.className = mode === v ? 'a' : '';
      });
    } else {
      const decKey = k === 'ome' ? 'd-ome' : `d-arch-${S.mode[0]}`;
      const dec = flowContainer.querySelector(`[data-okey="${decKey}"] .of-do`);
      if (dec) {
        dec.querySelectorAll('.of-b').forEach(b => {
          b.classList.toggle('a', b.textContent.trim().toLowerCase() === (v === 'yes' ? 'yes' : 'no'));
        });
      }
    }
  }

  function handleStateChange(k, v) {
    if (animating) return;
    if (k === 'mode') modeClicked = true;
    S[k] = v;
    updateControls(k, v);

    const newParts = buildParts();
    const newKeys = new Set(newParts.map(p => p.key));
    const exiting = [...prevKeys].filter(key => !newKeys.has(key));

    if (exiting.length > 0) {
      animating = true;
      let done = 0;
      const count = exiting.length;
      const els = flowContainer.querySelectorAll('[data-okey]');

      els.forEach(el => {
        if (exiting.includes(el.getAttribute('data-okey'))) {
          el.classList.add('of-exit');
          el.addEventListener('animationend', () => {
            done++;
            if (done >= count) {
              animating = false;
              doRender(newParts, newKeys);
            }
          }, { once: true });
        }
      });

      setTimeout(() => {
        if (done < count) {
          animating = false;
          doRender(newParts, newKeys);
        }
      }, 500);
    } else {
      doRender(newParts, newKeys);
    }
  }

  function renderPart(part) {
    switch (part.type) {
      case 'pill':
        return `<div class="of-pill">${part.text}</div>`;
      case 'connector':
        return `<div class="of-c ${part.cls || ''}"></div>`;
      case 'divider':
        return `<div class="of-dv"><span>${part.text}</span></div>`;
      case 'step':
        return `<div class="of-s"><div class="t">${part.title}</div>${part.desc ? `<div class="d">${part.desc}</div>` : ''}</div>`;
      case 'decision':
        const buttons = part.options.map(o => {
          const active = S[part.stateKey] === o.v ? 'a' : '';
          return `<button class="of-b ${active}" type="button" data-state="${part.stateKey}" data-value="${o.v}">${o.l}</button>`;
        }).join('');
        return `<div class="of-d"><div class="of-dl">${part.label}</div><div class="of-do">${buttons}</div></div>`;
      case 'mode':
        const pulse = !modeClicked ? 'pulse' : '';
        const standardClass = S.mode === 'standard' ? 'a' : '';
        const buildstreamClass = S.mode === 'buildstream' ? 'a' : '';
        let html = `<div class="of-m ${pulse}">`;
        html += `<button class="${standardClass}" type="button" data-mode="standard">Standard</button>`;
        html += `<button class="${buildstreamClass}" type="button" data-mode="buildstream">BuildStream</button>`;
        html += `</div>`;
        if (!modeClicked) html += `<div class="of-hint">↑ Click to switch deployment method</div>`;
        return html;
      default:
        return '';
    }
  }

  function buildParts() {
    const parts = [];
    const add = (type, key, extra) => parts.push({ type, key, ...extra });

    add('pill', 'start', { text: 'Start' });
    add('connector', 'c0', {});
    add('divider', 'dv-m', { text: 'Deployment Method' });
    add('connector', 'c0a', { cls: 'sm na' });
    add('mode', 'mode', {});
    add('connector', 'c0b', {});

    add('step', 's-build', { title: 'Build Omnia Images', desc: '<code>omnia-artifactory</code> repo' });
    add('connector', 'c1', {});
    add('step', 's-create', { title: 'Create Omnia Core Container', desc: '<code>omnia.sh</code>' });
    add('connector', 'c2', {});
    add('step', 's-login', { title: 'Log in to Core Container', desc: '<code>ssh omnia_core</code>' });
    add('connector', 'c3', {});
    add('step', 's-input', { title: 'Update Input Files', desc: '<code>/opt/omnia/input/project_default</code>' });
    add('connector', 'c4', {});

    add('decision', 'd-ome', {
      label: 'Discover nodes using OME?',
      options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
      stateKey: 'ome'
    });
    add('connector', 'c5', {});

    if (S.ome === 'yes') {
      add('step', 's-ome-y', { title: 'Generate PXE Mapping File via OME', desc: '<code>discovery.yml</code>' });
    } else {
      add('step', 's-ome-n', { title: 'Create PXE Mapping File Manually', desc: '<code>&lt;pxe_mapping_file_path.csv&gt;</code>' });
    }
    add('connector', 'c6', {});

    if (S.mode === 'standard') {
      add('step', 'ss-oim', { title: 'Deploy Containers on OIM', desc: '<code>prepare_oim.yml</code>' });
      add('connector', 'cs1', {});
      add('step', 'ss-pulp', { title: 'Download Packages to Pulp Repo', desc: '<code>local_repo.yml</code>' });
      add('connector', 'cs2', {});
      add('step', 'ss-img', { title: 'Build x86_64 Diskless Images', desc: '<code>build_image_x86_64.yml</code>' });
      add('connector', 'cs3', {});

      add('decision', 'd-arch-s', {
        label: 'aarch64 required?',
        options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
        stateKey: 'aarch64'
      });
      add('connector', 'cs4', {});

      if (S.aarch64 === 'yes') {
        add('step', 'ss-rhel', { title: 'Install RHEL10 on aarch64 Node', desc: '' });
        add('connector', 'cs5', {});
        add('step', 'ss-abuild', { title: 'Build aarch64 Diskless Images', desc: '<code>build_image_aarch64.yml</code>' });
        add('connector', 'cs6', {});
      }

      add('step', 'ss-prov', { title: 'Provision Nodes', desc: '<code>provision.yml</code>' });
      add('connector', 'cs7', {});
      add('step', 'ss-pxe', { title: 'PXE Boot Nodes', desc: '<code>set_pxe_boot.yml</code>' });
    }

    if (S.mode === 'buildstream') {
      add('decision', 'd-arch-b', {
        label: 'aarch64 Required?',
        options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
        stateKey: 'aarch64'
      });
      add('connector', 'cb1', {});

      if (S.aarch64 === 'yes') {
        add('step', 'sb-rhel', { title: 'Install RHEL10 on aarch64 Node', desc: '' });
        add('connector', 'cb2', {});
      }

      add('step', 'sb-oim', { title: 'Deploy BuildStreaM on OIM', desc: '<code>prepare_oim.yml</code>' });
      add('connector', 'cb3', {});
      add('step', 'sb-git', { title: 'Deploy GitLab', desc: '<code>gitlab.yml</code>' });
      add('connector', 'cb4', {});
      add('step', 'sb-cat', { title: 'Update Catalog', desc: 'GitLab' });
      add('connector', 'cb5', {});
      add('step', 'sb-ci', { title: 'Triggers Build Pipeline', desc: 'GitLab' });
      add('connector', 'cb6', {});
      add('step', 'sb-pxe', { title: 'Modify PXE Mapping File', desc: 'GitLab' });
      add('connector', 'cb7', {});
      add('step', 'sb-dep', { title: 'Triggers Deploy Pipeline', desc: 'GitLab' });
    }

    add('connector', 'cf0', {});
    add('divider', 'dv-fin', { text: 'Your cluster is now ready' });
    add('connector', 'cf1', { cls: 'sm na' });
    add('step', 's-telem', { title: 'Enable Telemetry', desc: '<code>telemetry.yml</code>' });
    add('connector', 'cf2', {});
    add('pill', 'end', { text: 'End' });

    return parts;
  }

  function doRender(parts, newKeys) {
    let delay = 0;

    const html = parts.map(p => {
      const brandNew = !isFirst && !prevKeys.has(p.key);
      if (brandNew) {
        const d = delay * 0.08;
        delay++;
        return `<div data-okey="${p.key}" class="of-new" style="animation-delay:${d}s">${renderPart(p)}</div>`;
      }
      return `<div data-okey="${p.key}">${renderPart(p)}</div>`;
    }).join('');

    prevKeys = newKeys;
    isFirst = false;
    flowContainer.innerHTML = html;
  }

  function init() {
    const parts = buildParts();
    const keys = new Set(parts.map(p => p.key));
    doRender(parts, keys);
  }

  // Event delegation for all interactive controls
  flowContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;

    if (btn.hasAttribute('data-mode')) {
      handleStateChange('mode', btn.getAttribute('data-mode'));
    } else if (btn.hasAttribute('data-state')) {
      handleStateChange(btn.getAttribute('data-state'), btn.getAttribute('data-value'));
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
