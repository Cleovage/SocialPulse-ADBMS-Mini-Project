/**
 * SocialPulse ADBMS Architecture & Query Optimization Lab
 * Handles explain plan execution, multi-stage pipeline runner, graph traversal, and index inspection
 */

// Switch sub-tabs in ADBMS Lab
function switchLabTab(tabName) {
  const tabs = ['explain', 'pipelines', 'graph', 'storage'];
  tabs.forEach(t => {
    const el = document.getElementById(`lab-tab-${t}`);
    const btn = document.getElementById(`labtab-${t}`);
    if (el) el.classList.toggle('hidden', t !== tabName);
    if (btn) {
      if (t === tabName) {
        btn.className = 'py-2.5 px-4 rounded-t-lg bg-indigo-600/20 text-indigo-300 border-b-2 border-indigo-500 font-semibold transition-all';
      } else {
        btn.className = 'py-2.5 px-4 rounded-t-lg text-gray-400 hover:text-white transition-all';
      }
    }
  });

  if (tabName === 'storage') {
    loadDatabaseStats();
  } else if (tabName === 'pipelines' && !window.lastPipelineLoaded) {
    runPipeline('bucketing');
  } else if (tabName === 'graph' && !window.lastGraphLoaded) {
    runGraphTraversal();
  }
}

/**
 * 1. SIDE-BY-SIDE EXPLAIN PLAN BENCHMARK (IXSCAN vs COLLSCAN)
 */
async function runExplainBenchmark() {
  const platform = document.getElementById('explain-platform').value;
  const minLikes = document.getElementById('explain-min-likes').value || 40000;

  const btn = (typeof event !== 'undefined' && event?.currentTarget) ? event.currentTarget : null;
  if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running...';

  try {
    const res = await fetch(`/api/adbms-lab/benchmarks/explain-plan?platform=${encodeURIComponent(platform)}&min_likes=${minLikes}`);
    const data = await res.json();

    const summary = data.benchmark_summary;
    const idx = summary.indexed_run;
    const coll = summary.unindexed_run;
    const gains = summary.adbms_performance_gain;

    // Update Indexed metrics
    document.getElementById('bench-idx-docs').innerText = idx.docs_examined.toLocaleString();
    document.getElementById('bench-idx-keys').innerText = idx.keys_examined.toLocaleString();
    document.getElementById('bench-idx-time').innerText = `${idx.execution_time_ms} ms`;

    // Update Unindexed / Collscan metrics
    document.getElementById('bench-coll-docs').innerText = coll.docs_examined.toLocaleString();
    document.getElementById('bench-coll-time').innerText = `${coll.execution_time_ms} ms`;

    // Update Banner Gains
    document.getElementById('bench-reduction-pct').innerText = gains.scan_reduction_pct;
    document.getElementById('bench-verdict-text').innerHTML = `
      <strong>Avoided scanning ${gains.unnecessary_docs_scanned_avoided.toLocaleString()} documents!</strong>
      ${gains.speedup_verdict}
    `;

    // Update Raw JSON inspection boxes
    document.getElementById('raw-explain-idx').innerText = JSON.stringify(data.raw_explain_indexed, null, 2);
    document.getElementById('raw-explain-coll').innerText = JSON.stringify(data.raw_explain_unindexed, null, 2);

    showToast(`Benchmark complete! Scan reduction: ${gains.scan_reduction_pct}`, 'success');
  } catch (err) {
    console.error('Benchmark failed:', err);
    showToast('Failed to run explain benchmark: ' + err.message, 'error');
  } finally {
    if (btn) btn.innerHTML = '<i class="fa-solid fa-bolt text-xs"></i><span>Run Benchmark</span>';
  }
}

/**
 * 2. INTERACTIVE AGGREGATION PIPELINE RUNNER
 */
async function runPipeline(type) {
  window.lastPipelineLoaded = type;
  
  // Highlight selected button without corrupting tab navigation buttons
  document.querySelectorAll('.pipeline-btn').forEach(b => {
    const isTarget = b.dataset.pipe === type || b.getAttribute('onclick')?.includes(`'${type}'`);
    if (isTarget) {
      b.className = 'pipeline-btn py-1.5 px-3 rounded bg-indigo-600 text-white font-semibold text-xs transition-all';
    } else {
      b.className = 'pipeline-btn py-1.5 px-3 rounded bg-dark-800 text-gray-300 hover:bg-dark-700 text-xs transition-all';
    }
  });

  const codeEl = document.getElementById('pipeline-code-display');
  const outputEl = document.getElementById('pipeline-output-display');
  const titleEl = document.getElementById('pipeline-title');
  const stagesEl = document.getElementById('pipeline-stages');
  const latencyEl = document.getElementById('pipeline-latency');

  codeEl.innerText = '// Fetching pipeline definition & executing on MongoDB...';
  outputEl.innerText = '// Awaiting server response...';
  latencyEl.innerText = 'executing...';

  let endpoint = '/api/adbms-lab/pipelines/bucketing';
  if (type === 'facet') endpoint = '/api/adbms-lab/pipelines/facet-multidimensional';
  if (type === 'lookup') endpoint = '/api/adbms-lab/pipelines/relational-lookup';
  if (type === 'graph') endpoint = '/api/adbms-lab/pipelines/graph-lookup?start_handle=@elena_ai_tech&max_depth=2';

  try {
    const res = await fetch(endpoint);
    const data = await res.json();

    titleEl.innerText = data.title;
    stagesEl.innerText = 'Stages: ' + (data.stages_used ? data.stages_used.join(', ') : 'Custom');
    latencyEl.innerText = `${data.execution_time_ms} ms`;

    codeEl.innerText = JSON.stringify(data.pipeline_code, null, 2);
    outputEl.innerText = JSON.stringify(data.results, null, 2);
  } catch (err) {
    codeEl.innerText = '// Error executing pipeline';
    outputEl.innerText = err.message;
    latencyEl.innerText = 'Error';
    showToast('Pipeline execution error', 'error');
  }
}

/**
 * 3. SOCIAL COLLABORATION GRAPH ($graphLookup)
 */
async function runGraphTraversal() {
  window.lastGraphLoaded = true;
  const startHandle = document.getElementById('graph-start-handle').value.trim() || '@elena_ai_tech';
  const depth = document.getElementById('graph-depth').value || 2;

  const rootNodeEl = document.getElementById('graph-root-node');
  const nodesGridEl = document.getElementById('graph-nodes-grid');
  const sizeEl = document.getElementById('graph-network-size');
  const latencyEl = document.getElementById('graph-latency');

  rootNodeEl.innerHTML = '<div class="text-xs text-gray-400 py-4 text-center w-full">Traversing MongoDB graph...</div>';
  nodesGridEl.innerHTML = '';

  try {
    const res = await fetch(`/api/adbms-lab/pipelines/graph-lookup?start_handle=${encodeURIComponent(startHandle)}&max_depth=${depth}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    const root = data.results;
    sizeEl.innerText = `${root.network_size} creators discovered`;
    latencyEl.innerText = `Execution: ${data.execution_time_ms} ms`;

    // Render Root Creator Card
    rootNodeEl.innerHTML = `
      <div class="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center text-white text-lg font-bold shrink-0 shadow-lg shadow-indigo-600/30">
        <i class="fa-solid fa-crown"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h5 class="text-sm font-bold text-white truncate">${root.name}</h5>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">ROOT (Hop 0)</span>
        </div>
        <p class="text-xs text-gray-400 font-mono">${root.handle}</p>
        <div class="flex items-center gap-3 text-[11px] text-gray-300 mt-1">
          <span><strong class="text-white">${(root.followers || 0).toLocaleString()}</strong> followers</span>
          <span>•</span>
          <span class="text-indigo-400 font-semibold">${root.niche}</span>
        </div>
      </div>
    `;

    // Render Connected Collaborators (Children nodes from $graphLookup)
    const collaborators = root.collaboration_network || [];
    if (collaborators.length === 0) {
      nodesGridEl.innerHTML = `<div class="col-span-full py-8 text-center text-xs text-gray-500">No outgoing collaboration edges recorded for ${startHandle}.</div>`;
      return;
    }

    nodesGridEl.innerHTML = collaborators.map(c => {
      const hopBadgeColor = c.hops === 0 
        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
        : (c.hops === 1 ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'bg-purple-500/10 text-purple-400 border-purple-500/30');

      return `
        <div class="glass-panel p-4 glass-panel-hover graph-node space-y-2 border border-white/5">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded border ${hopBadgeColor}">
              <i class="fa-solid fa-route mr-1"></i> Hop ${c.hops + 1}
            </span>
            <span class="text-[10px] text-gray-500 font-mono">${c.platform || 'Platform'}</span>
          </div>
          <div>
            <h6 class="text-xs font-bold text-white truncate">${c.name || c.handle}</h6>
            <p class="text-[11px] text-indigo-400 font-mono">${c.handle}</p>
          </div>
          <div class="pt-1 text-[11px] text-gray-400 flex items-center justify-between border-t border-white/5">
            <span>${c.niche || 'General'}</span>
            <span class="font-mono text-gray-200">${(c.followers || 0).toLocaleString()}</span>
          </div>
        </div>
      `;
    }).join('');

    showToast(`$graphLookup discovered ${root.network_size} creators at depth ${depth}`, 'info');
  } catch (err) {
    console.error('Graph traversal failed:', err);
    rootNodeEl.innerHTML = `<div class="text-xs text-rose-400 py-3 text-center w-full">Error: ${err.message}</div>`;
    showToast('Failed to traverse graph: ' + err.message, 'error');
  }
}

/**
 * 4. DATABASE & INDEX STORAGE INSPECTOR
 */
async function loadDatabaseStats() {
  const container = document.getElementById('collections-storage-list');
  if (!container) return;
  container.innerHTML = '<div class="text-xs text-gray-400 py-8 text-center">Loading MongoDB collections and index catalogs...</div>';

  try {
    const res = await fetch('/api/adbms-lab/database-stats');
    const data = await res.json();

    const collections = data.collections || [];

    container.innerHTML = collections.map(col => `
      <div class="glass-panel p-5 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/5">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-xs">
              <i class="fa-solid fa-table-cells"></i>
            </div>
            <div>
              <h5 class="text-sm font-bold text-white font-mono">${col.collection}</h5>
              <p class="text-[11px] text-gray-400">Namespace: ${data.database_name}.${col.collection}</p>
            </div>
          </div>
          <div class="flex items-center gap-4 text-xs font-mono">
            <div>
              <span class="text-gray-500">Documents:</span>
              <strong class="text-emerald-400 ml-1">${col.document_count.toLocaleString()}</strong>
            </div>
            <div>
              <span class="text-gray-500">Indexes:</span>
              <strong class="text-indigo-400 ml-1">${col.index_count}</strong>
            </div>
          </div>
        </div>

        <div>
          <span class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block mb-2 font-mono">Active Indexes:</span>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            ${col.indexes.map(idx => {
              const isUnique = idx.unique;
              const isTTL = idx.expireAfterSeconds !== null && idx.expireAfterSeconds !== undefined;
              const isPartial = idx.partialFilterExpression !== null && idx.partialFilterExpression !== undefined;
              const keyRepr = JSON.stringify(idx.key);

              let badge = 'B-Tree';
              if (keyRepr.includes('2dsphere')) badge = 'Geospatial 2dsphere';
              else if (keyRepr.includes('text')) badge = 'Full-Text ($text)';
              else if (isTTL) badge = `TTL (${idx.expireAfterSeconds}s)`;
              else if (isPartial) badge = 'Partial Filter';
              else if (Object.keys(idx.key || {}).length > 1) badge = 'Compound B-Tree';

              return `
                <div class="p-3 rounded-lg bg-dark-950/80 border border-white/5 text-xs space-y-1.5 font-mono">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-white text-[11px] truncate" title="${idx.name}">${idx.name}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${badge}</span>
                  </div>
                  <div class="text-[10px] text-gray-400 overflow-x-auto truncate" title='${keyRepr}'>
                    Key: ${keyRepr}
                  </div>
                  <div class="flex items-center gap-2 text-[10px] pt-1 border-t border-white/5">
                    ${isUnique ? '<span class="text-emerald-400 font-bold"><i class="fa-solid fa-lock text-[9px]"></i> Unique</span>' : '<span class="text-gray-600">Non-unique</span>'}
                    ${isTTL ? '<span class="text-cyan-400 ml-auto">Auto-expire: 24h</span>' : ''}
                    ${isPartial ? '<span class="text-amber-400 ml-auto">Filter: viral_score >= 75</span>' : ''}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>
    `).join('');

  } catch (err) {
    container.innerHTML = `<div class="text-xs text-rose-400 py-8 text-center">Error: ${err.message}</div>`;
  }
}
