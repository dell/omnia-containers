/* ****
 * Secure code generated utilizing Code Guardian.
 * Applicable rules used: CG-AI-002.1, CG-AI-002.2, CG-AI-002.6, CG-AI-002.8, CG-CONFIG-001.1, CG-CONFIG-001.5, CG-CRYPTO-001.1, CG-CRYPTO-001.2, CG-CRYPTO-001.3, CG-CRYPTO-001.5
 */

/**
 * Omnia Deployment Flow Interactive Chart
 */
(function(){
  const flowContainer = document.getElementById('omniaDeploymentFlowchart');
  if (!flowContainer) return;

  const S = { mode: 'standard', ome: 'no', aarch64: 'no', idractelemetry: 'no' };
  let prevKeys = new Set();
  let isFirst = true;
  let modeClicked = false;
  let animating = false;
  let tipBtn = null;

  const INFO = {
    aarch64: `
    <p><strong>Yes</strong>, if your cluster contains ARM64 (aarch64) nodes. In this case, a supported RHEL operating system must be installed on at least one supported ARM64 server, such as the PowerEdge XE8712. This server functions as the aarch64 image build node, which Omnia uses to create and customize provisioning images for ARM64-based Slurm compute and login/compiler nodes.</p>
    <p>The Slurm controller node and Kubernetes nodes can continue to run on the x86_64 architecture.</p>
    <p><strong>No</strong>, if all nodes in the cluster use the x86_64 architecture (Intel or AMD processors). In that scenario, an ARM64 image build node is not required.</p>
    <p class="of-ip-links"><a href="http://100.10.1.202:8000/en/omnia-docs-v2.3.0.0/Reference/SupportMatrix/operating_systems.html">Support matrix</a> &middot; <a href="http://100.10.1.202:8000/en/omnia-docs-v2.3.0.0/Reference/SupportMatrix/servers.html">Servers</a></p>`
  };

  const tip = document.createElement('div');
  tip.className = 'of-tip';
  tip.setAttribute('role', 'tooltip');
  tip.hidden = true;
  flowContainer.parentElement.appendChild(tip);

  function updateControls(k, v) {
    if (k === 'mode') {
      const buttons = flowContainer.querySelectorAll('.of-m button');
      buttons.forEach((btn, idx) => {
        const mode = idx === 0 ? 'standard' : 'buildstream';
        btn.className = mode === v ? 'a' : '';
      });
    } else {
      let decKey;
      if (k === 'ome') decKey = 'd-ome';
      else if (k === 'aarch64') decKey = `d-arch-${S.mode[0]}`;
      else if (k === 'idractelemetry') decKey = 'd-idrac-telemetry';
      const dec = flowContainer.querySelector(`[data-okey="${decKey}"] .of-do`);
      if (dec) {
        dec.querySelectorAll('.of-b').forEach(b => {
          b.classList.toggle('a', b.textContent.trim().toLowerCase() === (v === 'yes' ? 'yes' : 'no'));
        });
      }
    }
  }

  function handleStateChange(k, v) {
    closeTip();
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

  function closeTip() {
    if (tipBtn) {
      tipBtn.classList.remove('a');
      tipBtn.setAttribute('aria-expanded', 'false');
    }
    tipBtn = null;
    tip.hidden = true;
  }

  function toggleInfo(btn) {
    const same = tipBtn === btn;
    closeTip();
    if (same) return;
    tip.innerHTML = INFO[btn.getAttribute('data-info')];
    tip.hidden = false;
    tipBtn = btn;
    btn.classList.add('a');
    btn.setAttribute('aria-expanded', 'true');
    const box = tip.parentElement.getBoundingClientRect();
    const r = btn.getBoundingClientRect();
    const w = tip.offsetWidth, h = tip.offsetHeight;
    const x = r.left - box.left + r.width / 2 - w / 2;
    const flip = r.bottom + 8 + h > window.innerHeight && r.top - 8 - h > 0;
    const y = flip ? r.top - box.top - 8 - h : r.bottom - box.top + 8;
    tip.style.left = `${Math.max(0, Math.min(x, box.width - w))}px`;
    tip.style.top = `${y}px`;
  }

  function renderPart(part) {
    switch (part.type) {
      case 'pill':
        return `<div class="of-pill">${part.text}</div>`;
      case 'connector':
        return `<div class="of-c ${part.cls || ''}"></div>`;
      case 'divider':
        return `<div class="of-dv"><span>${part.text}</span></div>`;
      case 'step': {
        const hasDetails = part.details && part.details.href && part.details.text;
        let stepHtml = `<div class="of-s"><div class="t">${part.title}</div>`;
        if (part.desc) {
          stepHtml += `<div class="d">${part.desc}</div>`;
        }
        if (hasDetails) {
          stepHtml += `<div class="of-more"><a href="${part.details.href}" title="${part.details.title || part.details.text}">${part.details.text}</a></div>`;
        }
        stepHtml += '</div>';
        return stepHtml;
      }
      case 'decision': {
        const buttons = part.options.map(o => {
          const active = S[part.stateKey] === o.v ? 'a' : '';
          return `<button class="of-b ${active}" type="button" data-state="${part.stateKey}" data-value="${o.v}">${o.l}</button>`;
        }).join('');
        const infoBtn = part.info ? `<button class="of-i" type="button" data-info="${part.info}" aria-expanded="false" aria-label="More information">i</button>` : '';
        return `<div class="of-d"><div class="of-dl">${part.label}${infoBtn}</div><div class="of-do">${buttons}</div></div>`;
      }
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

    add('step', 's-create', { title: 'Set Up the OIM', desc: '<code>./omnia.sh --setup-venv</code>', details: { href: '../HowTo/main/setup_oim.html', text: 'Learn more: OIM setup >>' } });
    add('connector', 'c2', {});
    add('step', 's-login', { title: 'Activate the Omnia Environment', desc: '<code>source /opt/omnia/activate-omnia.sh</code>', details: { href: '../HowTo/main/configure_environment.html', text: 'Learn more: Main environment >>' } });
    add('connector', 'c3', {});
    add('step', 's-input', { title: 'Configure Domain Inputs', desc: '<code>&lt;OMNIA_DATA_PATH&gt;/&lt;domain&gt;/input/&lt;project&gt;</code>', details: { href: '../HowTo/index.html', text: 'Learn more: Domain guides >>' } });
    add('connector', 'c4', {});

    if (S.mode === 'buildstream') {
      add('step', 'sb-base', { title: 'Prepare Base Services', desc: '<code>./omnia.sh --prepare-base</code>', details: { href: '../HowTo/main/prepare_base.html', text: 'Learn more: Prepare base >>' } });
      add('connector', 'cb-base', {});
    }

    add('decision', 'd-ome', {
      label: 'Discover nodes using OME?',
      options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
      stateKey: 'ome'
    });
    add('connector', 'c5', {});

    if (S.ome === 'yes') {
      add('step', 's-ome-y', { title: 'Generate PXE Mapping File via OME', desc: '<code>./omnia.sh --run discovery</code>', details: { href: '../HowTo/discovery/discover_nodes.html', text: 'Learn more: Discover nodes >>' } });
    } else {
      add('step', 's-ome-n', { title: 'Create PXE Mapping File Manually', desc: '<code>&lt;pxe_mapping_file_path.csv&gt;</code>', details: { href: '../HowTo/discovery/create_mapping_file.html', text: 'Learn more: Create mapping >>' } });
    }
    add('connector', 'c6', {});

    if (S.mode === 'standard') {
      add('step', 'ss-pulp', { title: 'Prepare Local Repositories', desc: '<code>./omnia.sh --run repo_manager</code>', details: { href: '../HowTo/repo_manager/configure_repos.html', text: 'Learn more: Repository Manager >>' } });
      add('connector', 'cs2', {});

      add('decision', 'd-arch-s', {
        label: 'aarch64 required?',
        options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
        stateKey: 'aarch64',
        info: 'aarch64'
      });
      add('connector', 'cs4', {});

      if (S.aarch64 === 'yes') {
        add('step', 'ss-rhel', { title: 'Install RHEL on an aarch64 Node', desc: '<code>./omnia.sh --run utils --tags install_os</code>', details: { href: '../HowTo/utils/install_os_unattended.html', text: 'Learn more: Install RHEL >>' } });
        add('connector', 'cs5', {});
      }

      add('step', 'ss-img', { title: 'Build Diskless Images', desc: '<code>./omnia.sh --run image_build_manager</code>', details: { href: '../HowTo/image_build_manager/build_images.html', text: 'Learn more: Build OS images >>' } });
      add('connector', 'cs3', {});

      add('step', 'ss-prov', { title: 'Provision and PXE Boot Nodes', desc: '<code>./omnia.sh --run orchestrator</code>', details: { href: '../HowTo/orchestrator/provision_nodes.html', text: 'Learn more: Provision nodes >>' } });
    }

    if (S.mode === 'buildstream') {
      add('decision', 'd-arch-b', {
        label: 'aarch64 Required?',
        options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
        stateKey: 'aarch64',
        info: 'aarch64'
      });
      add('connector', 'cb1', {});

      add('step', 'sb-oim', { title: 'Deploy BuildStreaM and Configure GitLab', desc: '<code>./omnia.sh --run build_stream</code>', details: { href: '../HowTo/build_stream/index.html', text: 'Learn more: Deploy BuildStreaM >>' } });
      add('connector', 'cb3', {});

      if (S.aarch64 === 'yes') {
        add('step', 'sb-rhel', { title: 'Install RHEL10 on aarch64 Node', desc: '<code>./omnia.sh --run utils --tags install_os</code>', details: { href: '../HowTo/utils/install_os_unattended.html', text: 'Learn more: Install RHEL >>' } });
        add('connector', 'cb2', {});
      }

      add('step', 'sb-cat', { title: 'Update Catalog', desc: 'GitLab', details: { href: '../HowTo/build_stream/execute_build_pipeline.html', text: 'Learn more: Update catalog >>' } });
      add('connector', 'cb5', {});
      add('step', 'sb-ci', { title: 'Triggers Build Pipeline', desc: 'GitLab', details: { href: '../HowTo/build_stream/execute_build_pipeline.html', text: 'Learn more: Build pipeline >>' } });
      add('connector', 'cb6', {});
      add('step', 'sb-pxe', { title: 'Modify PXE Mapping File', desc: 'GitLab', details: { href: '../HowTo/build_stream/execute_deploy_pipeline.html', text: 'Learn more: PXE mapping >>' } });
      add('connector', 'cb7', {});
      add('step', 'sb-dep', { title: 'Triggers Deploy Pipeline', desc: 'GitLab', details: { href: '../HowTo/build_stream/execute_deploy_pipeline.html', text: 'Learn more: Deploy pipeline >>' } });
    }

    add('connector', 'cf0', {});
    add('divider', 'dv-fin', { text: 'Your cluster is now ready' });
    add('connector', 'cf1', { cls: 'sm na' });
    add('decision', 'd-idrac-telemetry', {
      label: 'Is telemetry required?',
      options: [{ l: 'Yes', v: 'yes' }, { l: 'No', v: 'no' }],
      stateKey: 'idractelemetry'
    });
    if (S.idractelemetry === 'yes') {
      add('connector', 'cf2', {});
      add('step', 's-telem', {
        title: 'Enable Telemetry',
        desc: '<code>./omnia.sh --run telemetry</code>',
        details: { href: '../HowTo/Telemetry/deploy_telemetry.html', text: 'Learn more: Deploy telemetry >>' }
      });
    }
    add('connector', 'cf3', {});
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
    } else if (btn.hasAttribute('data-info')) {
      toggleInfo(btn);
    }
  });

  document.addEventListener('click', (e) => {
    if (tipBtn && !e.target.closest('.of-i') && !tip.contains(e.target)) closeTip();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeTip();
  });
  window.addEventListener('resize', closeTip);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
