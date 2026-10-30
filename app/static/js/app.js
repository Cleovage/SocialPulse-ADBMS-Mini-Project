/**
 * SocialPulse Main Application Controller
 * Handles SPA navigation, views data binding, modals, maps, and transactions
 */

let activeView = 'overview';
let selectedForCompare = new Set();
let geoMap = null;
let geoCircle = null;
let geoMarkers = [];
let geoCartoTileLayer = null;
const DEFAULT_CARTO_KEY = 'cb1_4ezo_1_7d64896af4f435381c3f8b1a';
let clusterMarkers = [];
let searchDebounceTimeout = null;

// Initialize Application on Page Load
document.addEventListener('DOMContentLoaded', () => {
  switchView('overview');
  initGlobalSearch();
});

/**
 * Global Search in Topbar
 */
function initGlobalSearch() {
  const input = document.getElementById('global-search-input');
  if (!input) return;

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const val = input.value.trim();
      if (!val) return;
      if (val.startsWith('#')) {
        switchView('trends');
        filterTrendCategory('All');
        openTrendDetail(val);
      } else if (val.startsWith('@')) {
        switchView('instagram');
        fillAndSearchIg(val.replace(/^@/, ''));
      } else {
        switchView('influencers');
        document.getElementById('inf-search').value = val;
        loadInfluencers();
      }
    }
  });
}

/**
 * Toast Notifications
 */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const typeStyles = {
    info: 'bg-indigo-900/90 border-indigo-500/50 text-indigo-200',
    success: 'bg-emerald-900/90 border-emerald-500/50 text-emerald-200',
    error: 'bg-rose-900/90 border-rose-500/50 text-rose-200',
    warning: 'bg-amber-900/90 border-amber-500/50 text-amber-200'
  };

  const icons = {
    info: 'fa-circle-info',
    success: 'fa-circle-check',
    error: 'fa-triangle-exclamation',
    warning: 'fa-circle-exclamation'
  };

  toast.className = `p-3.5 rounded-lg border text-xs shadow-2xl backdrop-blur-md flex items-center gap-3 transition-all duration-300 transform translate-y-4 opacity-0 ${typeStyles[type] || typeStyles.info}`;
  toast.innerHTML = `
    <i class="fa-solid ${icons[type] || icons.info} text-sm"></i>
    <span class="font-medium">${message}</span>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-4');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Modal Utilities
 */
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}

// Close modals when clicking backdrop
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.add('hidden');
  }
});

/**
 * View Switcher
 */
function switchView(viewName) {
  activeView = viewName;
  const views = ['overview', 'influencers', 'instagram', 'trends', 'campaigns', 'geo', 'adbms-lab'];
  const titles = {
    overview: { title: 'Overview Dashboard', subtitle: 'Aggregated platform analytics & real-time KPIs' },
    influencers: { title: 'Influencer Discovery & Analytics', subtitle: 'B-Tree indexed search across creator demographics & engagement' },
    instagram: { title: 'Live Instagram Creator Lookup', subtitle: 'Real-time scraper, engagement rate calculator & MongoDB caching engine' },
    trends: { title: 'Trend Radar & Viral Velocity', subtitle: 'Real-time hashtag tracking with 24h progression & sentiment' },
    campaigns: { title: 'Campaign Planner & ACID Transactions', subtitle: 'Multi-document atomic budget allocation with rollback simulation' },
    geo: { title: 'Geospatial Analytics ($geoNear)', subtitle: 'Spherical distance queries powered by MongoDB 2dsphere indexes' },
    'adbms-lab': { title: 'ADBMS Architecture & Explain Lab', subtitle: 'Live query plan executionStats, recursive graph traversal, and benchmarks' }
  };

  // Toggle DOM views
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    const navBtn = document.getElementById(`nav-${v}`);
    if (el) el.classList.toggle('hidden', v !== viewName);
    if (navBtn) {
      if (v === viewName) {
        navBtn.classList.add('glass-nav-active');
      } else {
        navBtn.classList.remove('glass-nav-active');
      }
    }
  });

  // Update Topbar
  const meta = titles[viewName] || { title: viewName, subtitle: '' };
  document.getElementById('topbar-title').innerText = meta.title;
  document.getElementById('topbar-subtitle').innerText = meta.subtitle;

  // View-specific initializers
  if (viewName === 'overview') loadOverview();
  else if (viewName === 'influencers') loadInfluencers();
  else if (viewName === 'instagram') initInstagramLiveView();
  else if (viewName === 'trends') loadTrends();
  else if (viewName === 'campaigns') loadCampaigns();
  else if (viewName === 'geo') initGeoMap();
  else if (viewName === 'adbms-lab') switchLabTab('explain');
}

function refreshActiveView() {
  switchView(activeView);
  showToast(`Refreshed ${activeView} data`, 'info');
}

/**
 * Reseed Database Trigger
 */
async function triggerReseed() {
  const btn = document.getElementById('btn-reseed');
  if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Seeding...</span>';

  try {
    const res = await fetch('/api/adbms-lab/reseed', { method: 'POST' });
    const data = await res.json();
    showToast('Database successfully reseeded with fresh dataset!', 'success');
    refreshActiveView();
  } catch (err) {
    showToast('Reseed failed: ' + err.message, 'error');
  } finally {
    if (btn) btn.innerHTML = '<i class="fa-solid fa-arrows-rotate text-gray-400"></i><span>Reseed DB</span>';
  }
}

/**
 * ========================================================
 * VIEW 1: OVERVIEW DASHBOARD
 * ========================================================
 */
async function loadOverview() {
  try {
    const res = await fetch('/api/overview/stats');
    const data = await res.json();

    const kpis = data.kpis;
    document.getElementById('kpi-creators').innerText = (kpis.total_influencers || 0).toLocaleString();
    document.getElementById('kpi-posts').innerText = (kpis.total_posts || 0).toLocaleString();
    document.getElementById('kpi-er').innerText = `${kpis.avg_engagement_rate || 0}%`;
    document.getElementById('kpi-reach').innerText = formatCompactNumber(kpis.total_audience_reach || 0);

    // Render Charts
    renderTrendVelocityChart('chart-trend-velocity', data.top_surging_trends || []);
    renderPlatformDistributionChart('chart-platform-dist', data.platform_breakdown || []);

    // Render Niche Breakdown Table
    const nicheTbody = document.getElementById('overview-niche-tbody');
    const totalCreators = kpis.total_influencers || 1;
    nicheTbody.innerHTML = (data.niche_breakdown || []).map(n => {
      const pct = Math.round((n.count / totalCreators) * 100);
      return `
        <tr class="hover:bg-white/5 transition-colors">
          <td class="py-2.5 font-medium text-white flex items-center gap-2">
            <span class="w-2 h-2 rounded-full ${getNicheColor(n.niche)}"></span>
            ${n.niche}
          </td>
          <td class="py-2.5 font-mono text-gray-300">${n.count}</td>
          <td class="py-2.5 font-mono text-emerald-400 font-semibold">${n.avg_er}%</td>
          <td class="py-2.5 text-right">
            <div class="inline-flex items-center gap-2 w-24">
              <div class="flex-1 bg-dark-800 rounded-full h-1.5 overflow-hidden">
                <div class="bg-indigo-500 h-full rounded-full" style="width: ${pct}%"></div>
              </div>
              <span class="text-[10px] text-gray-400 font-mono">${pct}%</span>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Render Top Viral Posts
    const viralPostsList = document.getElementById('overview-top-posts');
    viralPostsList.innerHTML = (data.top_viral_posts || []).map(p => `
      <div class="p-3 rounded-lg bg-dark-800/80 border border-white/5 flex items-start justify-between gap-3 text-xs glass-panel-hover">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="font-bold text-white">${p.influencer_handle}</span>
            <span class="text-[10px] text-gray-400 font-mono">${p.platform}</span>
            <span class="text-[9px] px-1.5 py-0.2 rounded font-mono ${p.sentiment?.label === 'Positive' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-gray-700 text-gray-300'}">
              ${p.sentiment?.label || 'Neutral'}
            </span>
          </div>
          <p class="text-gray-300 text-[11px] line-clamp-1">${p.content}</p>
        </div>
        <div class="text-right shrink-0">
          <span class="text-xs font-bold font-mono text-rose-400 block">${p.metrics?.likes?.toLocaleString()} likes</span>
          <span class="text-[10px] text-indigo-400 font-mono">Viral: ${p.metrics?.viral_score || 0}/100</span>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Failed to load overview:', err);
    showToast('Error loading overview: ' + err.message, 'error');
  }
}

/**
 * ========================================================
 * VIEW 2: INFLUENCER DISCOVERY & ANALYTICS
 * ========================================================
 */
function debounceFilterInfluencers() {
  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(() => {
    loadInfluencers();
  }, 300);
}

async function loadInfluencers() {
  const search = document.getElementById('inf-search')?.value.trim();
  const niche = document.getElementById('filter-niche')?.value;
  const platform = document.getElementById('filter-platform')?.value;
  const tier = document.getElementById('filter-tier')?.value;
  const minEr = document.getElementById('filter-min-er')?.value;
  const minCred = document.getElementById('filter-min-cred')?.value;
  const sortBy = document.getElementById('filter-sort-by')?.value || 'metrics.followers_count';

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (niche && niche !== 'All') params.append('niche', niche);
  if (platform && platform !== 'All') params.append('platform', platform);
  if (tier && tier !== 'All') params.append('tier', tier);
  if (minEr) params.append('min_er', minEr);
  if (minCred) params.append('min_credibility', minCred);
  params.append('sort_by', sortBy);
  params.append('limit', 50);

  const grid = document.getElementById('influencer-grid');
  grid.innerHTML = '<div class="col-span-full py-12 text-center text-gray-500 text-xs">Querying MongoDB...</div>';

  try {
    const res = await fetch(`/api/influencers?${params.toString()}`);
    const data = await res.json();

    document.getElementById('influencer-total-count').innerText = data.total || 0;

    if (!data.data || data.data.length === 0) {
      grid.innerHTML = '<div class="col-span-full py-12 text-center text-gray-500 text-xs">No creators match your compound filter criteria.</div>';
      return;
    }

    grid.innerHTML = data.data.map(inf => {
      const isChecked = selectedForCompare.has(inf.handle) ? 'checked' : '';
      return `
        <div class="glass-panel p-5 glass-panel-hover flex flex-col justify-between space-y-4 relative border border-white/5">
          <!-- Top Row: Checkbox, Avatar, Handle, Platform -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <img src="${inf.avatar || 'https://randomuser.me/api/portraits/lego/1.jpg'}" alt="${inf.name}" class="w-12 h-12 rounded-xl object-cover border border-white/10 shrink-0">
              <div>
                <div class="flex items-center gap-1.5">
                  <h4 class="font-bold text-white text-sm hover:text-indigo-300 cursor-pointer" onclick="openCreatorDetail('${inf.handle}')">${inf.name}</h4>
                  <i class="fa-solid fa-circle-check text-indigo-400 text-[11px]"></i>
                </div>
                <p class="text-xs text-indigo-400 font-mono">${inf.handle}</p>
                <span class="text-[10px] text-gray-400 font-mono">${inf.platform_primary} • ${inf.location?.city || 'Global'}</span>
              </div>
            </div>
            
            <label class="flex items-center gap-1 text-[11px] text-gray-400 cursor-pointer select-none">
              <input type="checkbox" onchange="toggleCompare('${inf.handle}')" ${isChecked} class="rounded bg-dark-800 border-white/20 text-indigo-600 focus:ring-0">
              <span>Compare</span>
            </label>
          </div>

          <!-- Niche & Tier Badges -->
          <div class="flex items-center gap-2 text-[10px] font-mono">
            <span class="px-2 py-0.5 rounded border ${getNicheBadgeClass(inf.niche)}">${inf.niche}</span>
            <span class="px-2 py-0.5 rounded bg-dark-800 text-gray-300 border border-white/10">${inf.tier}</span>
          </div>

          <!-- Key Metrics Grid -->
          <div class="grid grid-cols-3 gap-2 pt-2 border-t border-white/5 text-center">
            <div class="p-2 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block font-mono">Followers</span>
              <span class="text-xs font-bold text-white font-mono">${formatCompactNumber(inf.metrics?.followers_count || 0)}</span>
            </div>
            <div class="p-2 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block font-mono">Eng. Rate</span>
              <span class="text-xs font-bold text-emerald-400 font-mono">${inf.metrics?.engagement_rate}%</span>
            </div>
            <div class="p-2 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block font-mono">Credibility</span>
              <span class="text-xs font-bold text-indigo-300 font-mono">${inf.metrics?.credibility_score}/100</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-between pt-2 text-xs">
            <div class="text-[11px] text-gray-400">
              Rate: <strong class="text-white font-mono">$${(inf.collaboration_rates?.post_rate_usd || 0).toLocaleString()}</strong> / post
            </div>
            <button onclick="openCreatorDetail('${inf.handle}')" class="py-1.5 px-3 rounded bg-indigo-600/30 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/40 font-medium transition-all text-xs">
              View Profile
            </button>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Failed to load influencers:', err);
    grid.innerHTML = `<div class="col-span-full py-12 text-center text-rose-400 text-xs">Error: ${err.message}</div>`;
  }
}

/**
 * Influencer Detail Modal
 */
async function openCreatorDetail(handle) {
  openModal('modal-influencer-detail');
  const container = document.getElementById('modal-detail-content');
  container.innerHTML = '<div class="py-16 text-center text-gray-400 text-xs">Loading profile breakdown...</div>';

  try {
    const res = await fetch(`/api/influencers/${encodeURIComponent(handle)}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    const inf = data.influencer;
    const posts = data.recent_posts || [];
    const contentBreakdown = data.content_breakdown || [];

    container.innerHTML = `
      <div class="space-y-6">
        <!-- Top Profile Banner -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div class="flex items-center gap-4">
            <img src="${inf.avatar || 'https://randomuser.me/api/portraits/lego/1.jpg'}" alt="${inf.name}" class="w-16 h-16 rounded-2xl object-cover border-2 border-indigo-500 shadow-lg shadow-indigo-600/20">
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-white">${inf.name}</h3>
                <span class="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${inf.tier}</span>
              </div>
              <p class="text-xs text-indigo-400 font-mono">${inf.handle}</p>
              <p class="text-xs text-gray-400 mt-1">${inf.bio || 'Digital creator'}</p>
            </div>
          </div>
          <div class="text-right space-y-1">
            <span class="text-[11px] text-gray-400 font-mono block">Estimated Fee</span>
            <span class="text-base font-bold text-emerald-400 font-mono">$${(inf.collaboration_rates?.reel_video_rate_usd || 0).toLocaleString()} / Reel</span>
            <span class="text-[10px] text-gray-500 block">Location: ${inf.location?.city}, ${inf.location?.country}</span>
          </div>
        </div>

        <!-- Demographics & Content Charts -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="glass-panel p-4 space-y-2">
            <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Performance & Demographics Radar</h5>
            <div class="h-44 relative">
              <canvas id="modal-chart-radar"></canvas>
            </div>
          </div>
          <div class="glass-panel p-4 space-y-2">
            <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Audience Age Distribution</h5>
            <div class="h-44 relative">
              <canvas id="modal-chart-age"></canvas>
            </div>
          </div>
          <div class="glass-panel p-4 space-y-2">
            <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Content Format Breakdown</h5>
            <div class="h-44 relative">
              <canvas id="modal-chart-content"></canvas>
            </div>
          </div>
        </div>

        <!-- Audience Split & Countries -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div class="p-4 rounded-xl bg-dark-950/80 border border-white/5 space-y-2">
            <span class="font-semibold text-gray-300 uppercase tracking-wider text-[11px] font-mono block">Gender Ratio</span>
            <div class="flex items-center gap-4 text-xs font-mono">
              <span class="text-indigo-400">Male: <strong>${inf.audience_demographics?.gender?.male}%</strong></span>
              <span class="text-pink-400">Female: <strong>${inf.audience_demographics?.gender?.female}%</strong></span>
              <span class="text-gray-400">Other: <strong>${inf.audience_demographics?.gender?.other}%</strong></span>
            </div>
          </div>
          <div class="p-4 rounded-xl bg-dark-950/80 border border-white/5 space-y-2">
            <span class="font-semibold text-gray-300 uppercase tracking-wider text-[11px] font-mono block">Top Audience Geos</span>
            <div class="flex flex-wrap gap-2 text-xs font-mono">
              ${(inf.audience_demographics?.top_countries || []).map(c => `
                <span class="px-2 py-0.5 rounded bg-dark-800 text-gray-200 border border-white/10">${c.country}: ${c.pct}%</span>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Recent Posts Feed -->
        <div class="space-y-3">
          <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Recent Posts Analyzed (${posts.length})</h5>
          <div class="space-y-2.5 max-h-60 overflow-y-auto pr-1">
            ${posts.map(p => `
              <div class="p-3 rounded-lg bg-dark-950/70 border border-white/5 flex items-start justify-between gap-3 text-xs">
                <div class="flex-1 min-w-0">
                  <p class="text-gray-200 line-clamp-2">${p.content}</p>
                  <div class="flex items-center gap-2 mt-1.5 text-[10px] text-gray-400 font-mono">
                    <span>${p.post_type}</span>
                    <span>•</span>
                    <span class="text-emerald-400">${p.sentiment?.label || 'Positive'} (${p.sentiment?.score})</span>
                    <span>•</span>
                    <span>${new Date(p.published_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div class="text-right shrink-0 font-mono">
                  <span class="text-white font-bold block">${(p.metrics?.likes || 0).toLocaleString()} likes</span>
                  <span class="text-indigo-400 text-[10px]">Viral: ${p.metrics?.viral_score || 0}</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    // Render Charts
    setTimeout(() => {
      renderCreatorDemographicsRadar('modal-chart-radar', inf);
      renderAgeDemographicsChart('modal-chart-age', inf.audience_demographics?.age_brackets || {});
      renderContentTypeChart('modal-chart-content', contentBreakdown);
    }, 50);

  } catch (err) {
    container.innerHTML = `<div class="py-16 text-center text-rose-400 text-xs">Failed to load: ${err.message}</div>`;
  }
}

/**
 * Head-to-Head Comparison
 */
function toggleCompare(handle) {
  if (selectedForCompare.has(handle)) {
    selectedForCompare.delete(handle);
  } else {
    if (selectedForCompare.size >= 4) {
      showToast('Maximum 4 creators can be compared side-by-side.', 'warning');
      return;
    }
    selectedForCompare.add(handle);
  }

  const count = selectedForCompare.size;
  document.getElementById('compare-count').innerText = count;
  const btn = document.getElementById('btn-compare-action');
  if (count >= 2) {
    btn.disabled = false;
    btn.className = 'py-2 px-3.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer';
  } else {
    btn.disabled = true;
    btn.className = 'py-2 px-3.5 rounded-lg text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-300 border border-white/10 flex items-center gap-2 transition-all opacity-50 cursor-not-allowed';
  }
}

async function launchComparisonModal() {
  if (selectedForCompare.size < 2) return;
  openModal('modal-comparison');
  const container = document.getElementById('modal-comparison-content');
  container.innerHTML = '<div class="py-16 text-center text-gray-400 text-xs">Fetching side-by-side comparison...</div>';

  const handles = Array.from(selectedForCompare).join(',');
  try {
    const res = await fetch(`/api/influencers/compare?handles=${encodeURIComponent(handles)}`);
    const data = await res.json();
    const comparison = data.comparison || [];

    container.innerHTML = `
      <div class="space-y-6 mt-4">
        <!-- Radar Benchmark Chart -->
        <div class="glass-panel p-5 space-y-2">
          <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Multi-Dimensional Normalized Radar Benchmark</h5>
          <div class="h-64 relative">
            <canvas id="modal-chart-radar-compare"></canvas>
          </div>
        </div>

        <!-- Comparative Metrics Table -->
        <div class="overflow-x-auto glass-panel p-4">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-white/10 text-gray-400 uppercase text-[10px] font-mono">
                <th class="py-3">Creator</th>
                <th class="py-3">Followers</th>
                <th class="py-3">Eng. Rate</th>
                <th class="py-3">Credibility</th>
                <th class="py-3">Post Rate</th>
                <th class="py-3">Sample Avg Likes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5 font-mono">
              ${comparison.map(item => {
                const inf = item.influencer;
                return `
                  <tr class="hover:bg-white/5 transition-colors">
                    <td class="py-3 font-medium text-white flex items-center gap-3">
                      <img src="${inf.avatar || ''}" class="w-8 h-8 rounded-lg object-cover border border-white/10">
                      <div>
                        <div class="font-bold">${inf.name}</div>
                        <div class="text-[10px] text-indigo-400">${inf.handle}</div>
                      </div>
                    </td>
                    <td class="py-3 text-gray-200 font-bold">${(inf.metrics?.followers_count || 0).toLocaleString()}</td>
                    <td class="py-3 text-emerald-400 font-bold">${inf.metrics?.engagement_rate}%</td>
                    <td class="py-3 text-indigo-300 font-bold">${inf.metrics?.credibility_score}/100</td>
                    <td class="py-3 text-white">$${(inf.collaboration_rates?.post_rate_usd || 0).toLocaleString()}</td>
                    <td class="py-3 text-cyan-400 font-bold">${item.computed_recent_avg_likes?.toLocaleString()}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    setTimeout(() => {
      renderComparisonRadarChart('modal-chart-radar-compare', comparison);
    }, 50);

  } catch (err) {
    container.innerHTML = `<div class="py-16 text-center text-rose-400 text-xs">Error: ${err.message}</div>`;
  }
}

/**
 * Add New Creator Modal
 */
function openAddCreatorModal() {
  openModal('modal-add-creator');
}

async function submitAddCreator(event) {
  event.preventDefault();
  const name = document.getElementById('add-name').value.trim();
  let handle = document.getElementById('add-handle').value.trim();
  if (!handle.startsWith('@')) handle = '@' + handle;

  const niche = document.getElementById('add-niche').value;
  const platform = document.getElementById('add-platform').value;
  const followers = parseInt(document.getElementById('add-followers').value, 10);
  const er = parseFloat(document.getElementById('add-er').value);
  const cred = parseInt(document.getElementById('add-cred').value, 10);
  const city = document.getElementById('add-city').value.trim() || 'San Francisco';
  const country = document.getElementById('add-country').value.trim() || 'USA';
  const bio = document.getElementById('add-bio').value.trim() || 'Creative digital creator.';

  // Determine tier
  let tier = 'Nano (1K-10K)';
  if (followers >= 1000000) tier = 'Mega (1M+)';
  else if (followers >= 500000) tier = 'Macro (500K-1M)';
  else if (followers >= 100000) tier = 'Mid-Tier (100K-500K)';
  else if (followers >= 10000) tier = 'Micro (10K-100K)';

  const payload = {
    handle: handle,
    name: name,
    avatar: 'https://randomuser.me/api/portraits/lego/2.jpg',
    bio: bio,
    niche: niche,
    platform_primary: platform,
    tier: tier,
    metrics: {
      followers_count: followers,
      following_count: 500,
      total_posts: 150,
      engagement_rate: er,
      avg_likes: Math.round(followers * (er / 100) * 0.85),
      avg_comments: Math.round(followers * (er / 100) * 0.15),
      credibility_score: cred,
      fake_followers_pct: 4.5
    },
    audience_demographics: {
      gender: { male: 52.0, female: 45.0, other: 3.0 },
      age_brackets: { '18-24': 35.0, '25-34': 45.0, '35-44': 15.0, '45+': 5.0 },
      top_countries: [{ country: 'US', pct: 40.0 }, { country: 'UK', pct: 20.0 }]
    },
    collaboration_rates: {
      post_rate_usd: Math.round(followers * 0.01),
      reel_video_rate_usd: Math.round(followers * 0.02)
    },
    location_geo: {
      type: 'Point',
      coordinates: [-122.4194, 37.7749]
    },
    location: {
      city: city,
      country: country
    }
  };

  try {
    const res = await fetch('/api/influencers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Failed to create creator');
    }

    closeModal('modal-add-creator');
    showToast(`Registered creator ${handle} into MongoDB!`, 'success');
    loadInfluencers();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

/**
 * ========================================================
 * VIEW 3: TREND RADAR & VELOCITY
 * ========================================================
 */
let activeTrendCategory = 'All';

function filterTrendCategory(cat) {
  activeTrendCategory = cat;
  document.querySelectorAll('.trend-cat-btn').forEach(btn => {
    if (btn.innerText.includes(cat) || (cat === 'All' && btn.innerText.includes('All Categories'))) {
      btn.className = 'trend-cat-btn px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium transition-all';
    } else {
      btn.className = 'trend-cat-btn px-3 py-1.5 rounded-lg bg-dark-800 text-gray-300 hover:bg-dark-700 transition-all';
    }
  });
  loadTrends();
}

async function loadTrends() {
  const sortBy = document.getElementById('trend-sort')?.value || 'velocity_score';
  const params = new URLSearchParams();
  if (activeTrendCategory && activeTrendCategory !== 'All') {
    params.append('category', activeTrendCategory);
  }
  params.append('sort_by', sortBy);

  const grid = document.getElementById('trends-grid');
  grid.innerHTML = '<div class="col-span-full py-12 text-center text-gray-500 text-xs">Loading trends...</div>';

  try {
    const res = await fetch(`/api/trends?${params.toString()}`);
    const data = await res.json();
    const trends = data.data || [];

    if (trends.length === 0) {
      grid.innerHTML = '<div class="col-span-full py-12 text-center text-gray-500 text-xs">No trending hashtags found in this category.</div>';
      return;
    }

    grid.innerHTML = trends.map(t => {
      const sentiment = t.sentiment_summary || { positive_pct: 70, neutral_pct: 20, negative_pct: 10 };
      const statusBadge = t.lifecycle_status === 'Surging' 
        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' 
        : (t.lifecycle_status === 'Emerging' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' : 'bg-gray-700 text-gray-300 border-white/10');

      return `
        <div onclick="openTrendDetail('${t.hashtag}')" class="glass-panel p-5 glass-panel-hover flex flex-col justify-between space-y-4 cursor-pointer border border-white/5">
          <!-- Top Row -->
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="flex items-center gap-2">
                <h4 class="font-bold text-white text-base hover:text-indigo-300">${t.hashtag}</h4>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded border ${statusBadge}">${t.lifecycle_status}</span>
              </div>
              <p class="text-xs text-gray-400 mt-0.5 line-clamp-1">${t.topic}</p>
            </div>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded border ${getNicheBadgeClass(t.category)}">${t.category}</span>
          </div>

          <!-- Viral Velocity Metric -->
          <div class="grid grid-cols-2 gap-3 pt-2 border-t border-white/5">
            <div class="p-2.5 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block font-mono">Velocity Score</span>
              <span class="text-sm font-bold text-cyan-400 font-mono">${t.velocity_score} pts/hr</span>
            </div>
            <div class="p-2.5 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block font-mono">24h Post Volume</span>
              <span class="text-sm font-bold text-white font-mono">${(t.volume_24h || 0).toLocaleString()}</span>
            </div>
          </div>

          <!-- Sentiment Bar -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-[11px] font-mono">
              <span class="text-gray-400">Audience Sentiment</span>
              <span class="text-emerald-400 font-bold">${sentiment.positive_pct}% Pos</span>
            </div>
            <div class="w-full h-1.5 rounded-full bg-dark-950 overflow-hidden flex">
              <div class="bg-emerald-500 h-full" style="width: ${sentiment.positive_pct}%" title="${sentiment.positive_pct}% Positive"></div>
              <div class="bg-gray-400 h-full" style="width: ${sentiment.neutral_pct}%" title="${sentiment.neutral_pct}% Neutral"></div>
              <div class="bg-rose-500 h-full" style="width: ${sentiment.negative_pct}%" title="${sentiment.negative_pct}% Negative"></div>
            </div>
          </div>

          <!-- Bottom: Key Influencers & View CTA -->
          <div class="flex items-center justify-between pt-2 border-t border-white/5 text-[11px]">
            <span class="text-gray-500 font-mono truncate max-w-[200px]">By: ${(t.top_influencer_handles || []).join(', ')}</span>
            <span class="text-indigo-400 font-medium">Deep Dive <i class="fa-solid fa-arrow-right text-[10px] ml-1"></i></span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    grid.innerHTML = `<div class="col-span-full py-12 text-center text-rose-400 text-xs">Error: ${err.message}</div>`;
  }
}

/**
 * Trend Detail Modal (Hourly Progression & Hashtag Post Lookup)
 */
async function openTrendDetail(hashtag) {
  openModal('modal-trend-detail');
  const container = document.getElementById('modal-trend-content');
  container.innerHTML = '<div class="py-16 text-center text-gray-400 text-xs">Loading hourly progression & matching posts...</div>';

  try {
    const cleanTag = hashtag.replace('#', '%23');
    const res = await fetch(`/api/trends/${cleanTag}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    const t = data.trend;
    const posts = data.viral_posts || [];

    container.innerHTML = `
      <div class="space-y-6">
        <!-- Top Info -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div class="flex items-center gap-3">
              <h3 class="text-xl font-bold text-white">${t.hashtag}</h3>
              <span class="text-xs font-mono px-2.5 py-0.5 rounded border ${getNicheBadgeClass(t.category)}">${t.category}</span>
            </div>
            <p class="text-xs text-gray-300 mt-1">${t.topic}</p>
          </div>
          <div class="text-right">
            <span class="text-xs text-gray-400 font-mono block">24h Total Posts</span>
            <span class="text-lg font-bold text-cyan-400 font-mono">${(t.volume_24h || 0).toLocaleString()}</span>
          </div>
        </div>

        <!-- 24-Hour Progression Chart -->
        <div class="glass-panel p-5 space-y-2">
          <div class="flex items-center justify-between">
            <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">24-Hour Velocity Progression Curve</h5>
            <span class="text-xs text-gray-400 font-mono">Hourly Volume Samples</span>
          </div>
          <div class="h-56 relative">
            <canvas id="modal-chart-hourly-trend"></canvas>
          </div>
        </div>

        <!-- Matching Posts via Multikey Index on hashtags -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h5 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Top Associated Posts (Multikey Index on 'hashtags')</h5>
            <span class="text-xs text-indigo-400 font-mono">${posts.length} indexed matches</span>
          </div>
          <div class="space-y-2.5 max-h-56 overflow-y-auto pr-1">
            ${posts.length > 0 ? posts.map(p => `
              <div class="p-3 rounded-lg bg-dark-950/70 border border-white/5 flex items-start justify-between gap-3 text-xs">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-bold text-white">${p.influencer_handle}</span>
                    <span class="text-[10px] text-gray-500 font-mono">${p.platform}</span>
                  </div>
                  <p class="text-gray-300 text-[11px] line-clamp-2">${p.content}</p>
                </div>
                <div class="text-right shrink-0 font-mono">
                  <span class="text-rose-400 font-bold block">${(p.metrics?.likes || 0).toLocaleString()} likes</span>
                  <span class="text-indigo-400 text-[10px]">Viral: ${p.metrics?.viral_score || 0}</span>
                </div>
              </div>
            `).join('') : `<div class="p-4 rounded-lg bg-dark-950/40 text-center text-xs text-gray-400">No matching posts found tagged with ${t.hashtag}</div>`}
          </div>
        </div>
      </div>
    `;

    setTimeout(() => {
      renderTrendHourlyProgressionChart('modal-chart-hourly-trend', t.hourly_history || []);
    }, 50);

  } catch (err) {
    container.innerHTML = `<div class="py-16 text-center text-rose-400 text-xs">Error: ${err.message}</div>`;
  }
}

/**
 * ========================================================
 * VIEW 4: CAMPAIGNS & ACID MULTI-DOCUMENT TRANSACTIONS
 * ========================================================
 */
async function loadCampaigns() {
  const list = document.getElementById('campaigns-list');
  const select = document.getElementById('tx-campaign-select');
  list.innerHTML = '<div class="col-span-full py-8 text-center text-gray-500 text-xs">Loading campaigns...</div>';

  try {
    const res = await fetch('/api/campaigns');
    const data = await res.json();
    const campaigns = data.data || [];

    // Populate transaction campaign select
    select.innerHTML = campaigns.map(c => `
      <option value="${c.id}">${c.brand_name} - ${c.campaign_title} (Rem: $${(c.total_budget - c.spent_budget).toLocaleString()})</option>
    `).join('');

    list.innerHTML = campaigns.map(c => {
      const budgetPct = Math.round((c.spent_budget / c.total_budget) * 100);
      return `
        <div class="glass-panel p-5 space-y-4 border border-white/5">
          <div class="flex items-start justify-between gap-3">
            <div>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${c.target_niche}</span>
              <h4 class="font-bold text-white text-base mt-1">${c.brand_name}: ${c.campaign_title}</h4>
            </div>
            <span class="text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/30">${c.status}</span>
          </div>

          <!-- Budget Progress -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="text-gray-400">Budget Allocated:</span>
              <span class="text-white font-bold">$${c.spent_budget?.toLocaleString()} / $${c.total_budget?.toLocaleString()}</span>
            </div>
            <div class="w-full h-2 rounded-full bg-dark-950 overflow-hidden">
              <div class="bg-indigo-500 h-full rounded-full transition-all duration-500" style="width: ${budgetPct}%"></div>
            </div>
          </div>

          <!-- KPIs -->
          <div class="grid grid-cols-3 gap-2 pt-2 border-t border-white/5 text-center text-xs font-mono">
            <div class="p-2 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block">Impressions</span>
              <span class="text-white font-bold">${formatCompactNumber(c.performance_kpis?.achieved_impressions || 0)}</span>
            </div>
            <div class="p-2 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block">Engagement</span>
              <span class="text-emerald-400 font-bold">${formatCompactNumber(c.performance_kpis?.achieved_engagement || 0)}</span>
            </div>
            <div class="p-2 rounded bg-dark-950/60">
              <span class="text-[10px] text-gray-400 block">Calculated ROI</span>
              <span class="text-cyan-400 font-bold">${c.performance_kpis?.calculated_roi}x</span>
            </div>
          </div>

          <!-- Contracted Influencers -->
          <div class="text-[11px] text-gray-400 border-t border-white/5 pt-2 flex items-center justify-between">
            <span>Contracted Creators: <strong class="text-gray-200">${c.assigned_influencers?.length || 0}</strong></span>
            <span class="text-gray-500 font-mono">${(c.assigned_influencers || []).map(a => a.handle).slice(0, 3).join(', ')}</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    list.innerHTML = `<div class="col-span-full py-8 text-center text-rose-400 text-xs">Error: ${err.message}</div>`;
  }
}

/**
 * Campaign Matchmaker
 */
async function runMatchmaker() {
  const niche = document.getElementById('match-niche').value;
  const budget = document.getElementById('match-budget').value || 15000;
  const cred = document.getElementById('match-cred').value || 90;

  const container = document.getElementById('matchmaker-results');
  container.innerHTML = '<div class="py-6 text-center text-gray-400 text-xs">Executing MongoDB Matchmaker algorithm...</div>';

  try {
    const res = await fetch(`/api/campaigns/matchmaker?niche=${encodeURIComponent(niche)}&max_budget_per_creator=${budget}&min_credibility=${cred}`);
    const data = await res.json();
    const matches = data.matches || [];

    if (matches.length === 0) {
      container.innerHTML = '<p class="text-xs text-gray-400 py-4">No creators found matching these strict budget and credibility thresholds.</p>';
      return;
    }

    container.innerHTML = `
      <div class="space-y-3 pt-2">
        <span class="text-xs font-mono text-emerald-400 font-semibold block">Found ${matches.length} Optimal Creators Ranked by Engagement Rate:</span>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          ${matches.map(inf => `
            <div class="p-3.5 rounded-lg bg-dark-950/80 border border-white/5 flex items-center justify-between gap-3 text-xs">
              <div class="flex items-center gap-3">
                <img src="${inf.avatar || ''}" class="w-10 h-10 rounded-lg object-cover">
                <div>
                  <h6 class="font-bold text-white">${inf.name}</h6>
                  <p class="text-[11px] text-indigo-400 font-mono">${inf.handle}</p>
                  <span class="text-[10px] text-gray-400">${inf.metrics?.followers_count?.toLocaleString()} followers</span>
                </div>
              </div>
              <div class="text-right">
                <span class="text-emerald-400 font-bold font-mono block">${inf.metrics?.engagement_rate}% ER</span>
                <span class="text-[11px] text-gray-300 font-mono">$${inf.collaboration_rates?.reel_video_rate_usd?.toLocaleString()}</span>
                <button onclick="prefillTransaction('${inf.handle}', ${inf.collaboration_rates?.reel_video_rate_usd || 5000})" class="mt-1 text-[10px] px-2 py-0.5 rounded bg-indigo-600/40 text-indigo-200 hover:bg-indigo-600 transition-all font-mono">
                  Select for Tx
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

  } catch (err) {
    container.innerHTML = `<div class="py-4 text-center text-rose-400 text-xs">Error: ${err.message}</div>`;
  }
}

function prefillTransaction(handle, fee) {
  document.getElementById('tx-handle').value = handle;
  document.getElementById('tx-fee').value = fee;
  document.getElementById('tx-handle').scrollIntoView({ behavior: 'smooth' });
  showToast(`Prefilled transaction for ${handle}`, 'info');
}

/**
 * Execute Multi-Document ACID Transaction
 */
async function executeTransaction(isRollback) {
  const campaignId = document.getElementById('tx-campaign-select').value;
  const handle = document.getElementById('tx-handle').value.trim();
  const fee = parseFloat(document.getElementById('tx-fee').value);

  const statusBadge = document.getElementById('tx-status-badge');
  const terminal = document.getElementById('tx-terminal-output');

  statusBadge.innerText = 'EXECUTING TRANSACTION...';
  statusBadge.className = 'text-amber-400 font-mono animate-pulse';
  terminal.innerText = `// Starting session.start_transaction()...\n// Target Campaign ID: ${campaignId}\n// Creator: ${handle}\n// Fee: $${fee}\n// Simulate Rollback: ${isRollback}\n// Awaiting MongoDB execution...`;

  try {
    const res = await fetch('/api/campaigns/allocate-budget-transaction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_id: campaignId,
        influencer_handle: handle,
        fee: fee,
        simulate_rollback: isRollback
      })
    });

    const data = await res.json();

    if (!res.ok) {
      statusBadge.innerText = 'TRANSACTION FAILED';
      statusBadge.className = 'text-rose-400 font-mono font-bold';
      terminal.innerText = `// ERROR:\n${JSON.stringify(data, null, 2)}`;
      showToast(data.detail || 'Transaction failed', 'error');
      return;
    }

    if (data.status === 'aborted') {
      statusBadge.innerText = 'TRANSACTION ABORTED (ROLLED BACK)';
      statusBadge.className = 'text-rose-400 font-mono font-bold';
      showToast('Atomic Rollback simulated! No partial state persisted.', 'warning');
    } else {
      statusBadge.innerText = 'TRANSACTION COMMITTED';
      statusBadge.className = 'text-emerald-400 font-mono font-bold';
      showToast(`Transaction committed! Allocated $${fee} to ${handle}`, 'success');
      loadCampaigns(); // Refresh budget cards
    }

    terminal.innerText = JSON.stringify(data, null, 2);

  } catch (err) {
    statusBadge.innerText = 'ERROR';
    statusBadge.className = 'text-rose-400 font-mono font-bold';
    terminal.innerText = `// NETWORK/EXECUTION ERROR:\n${err.message}`;
    showToast('Transaction execution error', 'error');
  }
}

/**
 * ========================================================
 * VIEW 5: GEOSPATIAL HEATMAP ($geoNear)
 * ========================================================
 */

/**
 * ========================================================
 * CARTO MAP API KEY MANAGEMENT
 * ========================================================
 */
function getActiveCartoKey() {
  const local = localStorage.getItem('socialpulse_carto_api_key');
  if (local && local.trim()) return local.trim();
  return DEFAULT_CARTO_KEY;
}

function updateCartoTileLayer(key) {
  const activeKey = (key !== undefined && key !== null) ? key.trim() : getActiveCartoKey();
  if (geoCartoTileLayer && geoMap) {
    geoMap.removeLayer(geoCartoTileLayer);
  }
  const tileUrl = activeKey
    ? `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=${encodeURIComponent(activeKey)}`
    : `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`;

  geoCartoTileLayer = L.tileLayer(tileUrl, {
    maxZoom: 19,
    subdomains: 'abcd',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
  });

  if (geoMap) {
    geoCartoTileLayer.addTo(geoMap);
  }
  updateCartoKeyUI(activeKey);
}

function updateCartoKeyUI(key) {
  const activeKey = key || getActiveCartoKey();
  const preview = activeKey.length > 12 ? `${activeKey.slice(0, 8)}...${activeKey.slice(-4)}` : activeKey;
  const previewEl = document.getElementById('carto-modal-key-preview');
  if (previewEl) previewEl.innerText = preview || 'None';

  const mapBtnText = document.getElementById('map-key-btn-text');
  if (mapBtnText) mapBtnText.innerText = `Key: ${activeKey.slice(0, 7)}...`;
}

function openCartoKeyModal() {
  const activeKey = getActiveCartoKey();
  const input = document.getElementById('input-carto-api-key');
  if (input) input.value = activeKey;
  updateCartoKeyUI(activeKey);
  openModal('modal-carto-key');
}

async function handleSaveCartoKey(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('input-carto-api-key');
  const key = (input ? input.value : '').trim();
  if (!key) {
    showToast('Please enter a valid CARTO API Key', 'error');
    return;
  }
  localStorage.setItem('socialpulse_carto_api_key', key);
  updateCartoTileLayer(key);
  closeModal('modal-carto-key');
  showToast('CARTO Map API Key applied and tiles refreshed!', 'success');

  try {
    await fetch('/api/geo/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key })
    });
  } catch (err) {
    console.warn('Backend sync for carto key:', err);
  }
}

async function resetDefaultCartoKey() {
  localStorage.removeItem('socialpulse_carto_api_key');
  const input = document.getElementById('input-carto-api-key');
  if (input) input.value = DEFAULT_CARTO_KEY;
  updateCartoTileLayer(DEFAULT_CARTO_KEY);
  closeModal('modal-carto-key');
  showToast('Reset CARTO API Key to default benchmark key!', 'info');

  try {
    await fetch('/api/geo/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: DEFAULT_CARTO_KEY })
    });
  } catch (err) {
    console.warn('Backend reset for carto key:', err);
  }
}

async function pasteCartoKeyFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      const input = document.getElementById('input-carto-api-key');
      if (input) input.value = text.trim();
      showToast('Pasted key from clipboard!', 'info');
    }
  } catch (err) {
    showToast('Unable to read clipboard. Please paste manually.', 'error');
  }
}

async function initGeoMap() {
  if (geoMap) {
    setTimeout(() => geoMap.invalidateSize(), 200);
    return;
  }

  // Initialize Leaflet Map centered at San Francisco
  geoMap = L.map('geo-map', {
    zoomControl: true,
    attributionControl: false
  }).setView([37.7749, -122.4194], 3);

  // Apply CartoDB DarkMatter Tile Layer with Active API Key
  updateCartoTileLayer();

  // Load Global Hubs Buttons
  loadGlobalHubs();

  // Load Influencer Geographic Clusters
  loadInfluencerClusters();

  // Execute initial $geoNear query
  runGeoNearQuery();
}

async function loadGlobalHubs() {
  const container = document.getElementById('geo-hub-buttons');
  if (!container) return;

  try {
    const res = await fetch('/api/geo/hubs');
    const hubs = await res.json();

    container.innerHTML = hubs.map(h => `
      <button onclick="selectHub(${h.lng}, ${h.lat}, '${h.city}')" class="py-1 px-2.5 rounded bg-dark-800 hover:bg-indigo-600/40 text-gray-300 hover:text-white border border-white/10 transition-all font-mono text-[11px]">
        <i class="fa-solid fa-location-dot text-indigo-400 mr-1"></i>${h.city}
      </button>
    `).join('');
  } catch (err) {
    console.error('Failed to load hubs:', err);
  }
}

function selectHub(lng, lat, city) {
  document.getElementById('geo-lng').value = lng;
  document.getElementById('geo-lat').value = lat;
  geoMap.setView([lat, lng], 6);
  runGeoNearQuery();
  showToast(`Centered map on ${city}`, 'info');
}

async function loadInfluencerClusters() {
  try {
    const res = await fetch('/api/geo/influencer-clusters');
    const clusters = await res.json();

    clusters.forEach(c => {
      const coords = c.coordinates;
      if (!coords || coords.length < 2) return;

      const marker = L.circleMarker([coords[1], coords[0]], {
        radius: Math.min(20, Math.max(8, c.creators_count * 2.5)),
        fillColor: '#6366f1',
        color: '#818cf8',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.5
      }).addTo(geoMap);

      marker.bindPopup(`
        <div class="text-xs p-1 space-y-1">
          <strong class="text-white text-sm font-bold block">${c.city}, ${c.country}</strong>
          <div class="text-indigo-400 font-mono">${c.creators_count} Tracked Creators</div>
          <div class="text-gray-300 text-[11px]">Combined Reach: ${(c.total_followers || 0).toLocaleString()}</div>
          <div class="text-emerald-400 text-[11px]">Avg ER: ${c.avg_engagement_rate}%</div>
          <div class="text-[10px] text-gray-400 pt-1 border-t border-white/10">Top: ${(c.top_handles || []).join(', ')}</div>
        </div>
      `);
      clusterMarkers.push(marker);
    });
  } catch (err) {
    console.error('Failed to load clusters:', err);
  }
}

async function runGeoNearQuery() {
  const lng = parseFloat(document.getElementById('geo-lng').value);
  const lat = parseFloat(document.getElementById('geo-lat').value);
  const radiusKm = parseFloat(document.getElementById('geo-radius').value);

  // Clear previous query markers
  geoMarkers.forEach(m => geoMap.removeLayer(m));
  geoMarkers = [];
  if (geoCircle) geoMap.removeLayer(geoCircle);

  // Draw Radius Circle on Leaflet
  geoCircle = L.circle([lat, lng], {
    radius: radiusKm * 1000,
    color: '#06b6d4',
    fillColor: '#06b6d4',
    fillOpacity: 0.08,
    weight: 1.5,
    dashArray: '4, 4'
  }).addTo(geoMap);

  const postsListEl = document.getElementById('geo-posts-list');
  postsListEl.innerHTML = '<div class="text-xs text-gray-500 text-center py-12">Executing MongoDB $geoNear pipeline...</div>';

  try {
    const res = await fetch(`/api/geo/near?lng=${lng}&lat=${lat}&max_distance_km=${radiusKm}&limit=25`);
    const data = await res.json();
    const posts = data.posts || [];

    document.getElementById('geo-posts-count').innerText = `${posts.length} posts found`;

    if (posts.length === 0) {
      postsListEl.innerHTML = '<p class="text-xs text-gray-400 text-center py-12">No posts found within this radius. Try increasing the distance slider.</p>';
      return;
    }

    // Add markers and populate sidebar
    postsListEl.innerHTML = posts.map(p => {
      const coords = p.location?.coordinates;
      if (coords && coords.length >= 2) {
        const marker = L.circleMarker([coords[1], coords[0]], {
          radius: 5,
          fillColor: '#06b6d4',
          color: '#ffffff',
          weight: 1,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(geoMap);

        marker.bindPopup(`
          <div class="text-xs space-y-1">
            <strong class="text-white block">${p.influencer_handle} (${p.platform})</strong>
            <p class="text-gray-300 text-[11px]">${p.content}</p>
            <div class="text-cyan-400 font-mono text-[10px]">Distance: ${p.distance_km} km</div>
          </div>
        `);
        geoMarkers.push(marker);
      }

      return `
        <div class="p-3 rounded-lg bg-dark-950/70 border border-white/5 space-y-1 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white">${p.influencer_handle}</span>
            <span class="text-cyan-400 font-mono text-[10px]">${p.distance_km} km away</span>
          </div>
          <p class="text-gray-300 text-[11px] line-clamp-2">${p.content}</p>
          <div class="flex items-center justify-between text-[10px] text-gray-400 pt-1 font-mono">
            <span>${p.platform}</span>
            <span class="text-rose-400 font-bold">${(p.metrics?.likes || 0).toLocaleString()} likes</span>
          </div>
        </div>
      `;
    }).join('');

    showToast(`$geoNear found ${posts.length} posts within ${radiusKm}km`, 'info');

  } catch (err) {
    postsListEl.innerHTML = `<div class="text-xs text-rose-400 text-center py-12">Error: ${err.message}</div>`;
  }
}

/**
 * Helper Formatting Functions
 */
function formatCompactNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

function getNicheColor(niche) {
  const map = {
    'Tech & AI': 'bg-indigo-500',
    'Fashion & Lifestyle': 'bg-pink-500',
    'Gaming & Esports': 'bg-purple-500',
    'Health & Fitness': 'bg-emerald-500',
    'Finance & Crypto': 'bg-amber-500',
    'Food & Culinary': 'bg-orange-500',
    'Travel & Adventure': 'bg-cyan-500'
  };
  return map[niche] || 'bg-gray-500';
}

function getNicheBadgeClass(niche) {
  const map = {
    'Tech & AI': 'badge-tech',
    'Fashion & Lifestyle': 'badge-fashion',
    'Gaming & Esports': 'badge-gaming',
    'Health & Fitness': 'badge-fitness',
    'Finance & Crypto': 'badge-finance',
    'Food & Culinary': 'badge-food',
    'Travel & Adventure': 'badge-travel'
  };
  return map[niche] || 'badge-tech';
}

/* ==========================================================================
   Live Instagram Creator Lookup & Caching Controller
   ========================================================================== */

let igSearchInitialized = false;

function initInstagramLiveView() {
  if (!igSearchInitialized) {
    const input = document.getElementById('ig-search-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          handleInstagramSearch();
        }
      });
    }
    igSearchInitialized = true;
  }
  loadInstagramConfig();
}

function handleInstagramSearch() {
  const input = document.getElementById('ig-search-input');
  if (!input) return;
  const username = input.value.trim();
  searchInstagram(username);
}

function fillAndSearchIg(username) {
  const input = document.getElementById('ig-search-input');
  if (input) {
    input.value = username;
  }
  searchInstagram(username);
}

async function searchInstagram(username, forceRefresh = false) {
  const cleanUser = (username || '').trim().replace(/^@/, '');
  if (!cleanUser) {
    showToast('Please enter an Instagram username', 'warning');
    return;
  }

  // DOM elements
  const initialEl = document.getElementById('ig-initial-state');
  const skeletonEl = document.getElementById('ig-loading-skeleton');
  const cardEl = document.getElementById('ig-profile-card');
  const errorEl = document.getElementById('ig-error-fallback');
  const statusEl = document.getElementById('ig-skeleton-status');

  if (initialEl) initialEl.classList.add('hidden');
  if (cardEl) cardEl.classList.add('hidden');
  if (errorEl) errorEl.classList.add('hidden');
  if (skeletonEl) skeletonEl.classList.remove('hidden');

  // Multi-step animated progress indicators
  let stepIndex = 0;
  const steps = [
    `Connecting to Instagram multi-tier scraper for @${cleanUser}...`,
    'Parsing public creator metadata, bio, followers & media count...',
    'Analyzing recent post metrics and calculating Engagement Rate (ER)...',
    'Persisting profile document into MongoDB cache...'
  ];
  if (statusEl) statusEl.innerText = steps[0];
  const stepTimer = setInterval(() => {
    stepIndex = (stepIndex + 1) % steps.length;
    if (statusEl) statusEl.innerText = steps[stepIndex];
  }, 700);

  try {
    const url = `/api/instagram/profile/${encodeURIComponent(cleanUser)}${forceRefresh ? '?force_refresh=true' : ''}`;
    const res = await fetch(url);
    clearInterval(stepTimer);

    if (skeletonEl) skeletonEl.classList.add('hidden');

    if (!res.ok) {
      let errMsg = `Unable to fetch profile for @${cleanUser}`;
      try {
        const errJson = await res.json();
        errMsg = errJson.error || errJson.detail || errMsg;
      } catch (e) {}
      renderInstagramError(errMsg, cleanUser);
      return;
    }

    const data = await res.json();
    if (data.status === 'error') {
      renderInstagramError(data.error || data.detail || 'Profile not found', cleanUser);
      return;
    }

    renderInstagramProfileCard(data);
    showToast(`Loaded @${cleanUser} (${data.source === 'cached_instagram' ? 'from MongoDB cache' : 'live fetch'})`, 'success');

  } catch (err) {
    clearInterval(stepTimer);
    if (skeletonEl) skeletonEl.classList.add('hidden');
    renderInstagramError(err.message || 'Network request failed while contacting server', cleanUser);
  }
}

function formatRelativeTime(seconds) {
  if (seconds === null || seconds === undefined) return 'live';
  if (seconds < 60) return 'just now';
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function renderInstagramProfileCard(data) {
  const cardEl = document.getElementById('ig-profile-card');
  if (!cardEl) return;

  const username = data.username || '';
  const fullName = data.full_name || username;
  const bio = data.bio || 'No bio provided.';
  const isVerified = Boolean(data.is_verified);
  const isPrivate = Boolean(data.is_private);
  const source = data.source || 'live_instagram';
  const cachedAgo = data.cached_seconds_ago !== undefined ? data.cached_seconds_ago : 0;
  const metrics = data.metrics || {};

  const followers = metrics.followers_count || 0;
  const following = metrics.following_count || 0;
  const postsCount = metrics.posts_count || 0;
  const avgLikes = metrics.avg_likes || 0;
  const avgComments = metrics.avg_comments || 0;
  const er = typeof metrics.engagement_rate === 'number' ? metrics.engagement_rate : 0.0;
  const erMethod = metrics.er_calculation_method || 'exact_post_metrics';

  // ER Health badge
  let erBadge = '<span class="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">High Engagement (&gt; 3.5%)</span>';
  if (er < 1.5) {
    erBadge = '<span class="text-xs px-2.5 py-1 rounded-full bg-gray-700/60 text-gray-300 border border-white/10 font-semibold">Normalized Mega-Tier (&lt; 1.5%)</span>';
  } else if (er < 3.5) {
    erBadge = '<span class="text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">Average Engagement (1.5% - 3.5%)</span>';
  }

  // Cache badge
  let cacheBadgeHtml = '';
  if (source === 'live_instagram') {
    cacheBadgeHtml = `
      <span class="px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm">
        <span class="w-2 h-2 rounded-full bg-emerald-400 pulse-emerald"></span>
        ⚡ LIVE FETCH FROM INSTAGRAM
      </span>
    `;
  } else if (source === 'cached_instagram') {
    cacheBadgeHtml = `
      <span class="px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 shadow-sm">
        <i class="fa-solid fa-database text-indigo-400"></i>
        💾 CACHED IN MONGODB (${formatRelativeTime(cachedAgo)})
      </span>
    `;
  } else {
    cacheBadgeHtml = `
      <span class="px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 shadow-sm">
        <i class="fa-solid fa-server text-amber-400"></i>
        LOCAL SYNTHETIC BENCHMARK
      </span>
    `;
  }

  // Avatar with fallback
  const fallbackAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(fullName)}&background=ec4899&color=fff&size=160`;
  const avatarUrl = data.profile_pic_url || fallbackAvatar;

  // Recent posts HTML
  let mediaHtml = '';
  const posts = data.recent_posts || [];
  if (posts.length > 0) {
    const postCards = posts.slice(0, 6).map((p, idx) => {
      const pLikesNum = (p.likes !== undefined && p.likes !== null && p.likes > 0) ? p.likes : (avgLikes || 1000);
      const pCommentsNum = (p.comments !== undefined && p.comments !== null && p.comments > 0) ? p.comments : (avgComments || 50);
      const pLikes = formatCompactNumber(pLikesNum);
      const pComments = formatCompactNumber(pCommentsNum);
      const pThumb = p.thumbnail || '';
      const pUrl = p.url || `https://instagram.com/${username}`;
      const pType = p.post_type || (idx % 2 === 0 ? 'Video' : 'Image');
      const isVideo = pType === 'Video' || pType === 'Reel';
      const pCap = (p.caption || '').replace(/"/g, '&quot;');

      return `
        <a href="${pUrl}" target="_blank" rel="noopener noreferrer" class="group relative rounded-xl overflow-hidden bg-dark-950 border border-white/10 hover:border-pink-500/50 transition-all aspect-square block shadow-lg">
          ${pThumb ? `
            <img src="${pThumb}" 
                 data-orig-src="${pThumb}" 
                 referrerpolicy="no-referrer" 
                 onerror="if (!this.dataset.proxied && this.dataset.origSrc && this.dataset.origSrc.startsWith('http')) { this.dataset.proxied = '1'; this.src = '/api/instagram/proxy-image?url=' + encodeURIComponent(this.dataset.origSrc); } else { this.style.display='none'; this.nextElementSibling.classList.remove('hidden'); }" 
                 alt="${pCap || (isVideo ? 'Instagram Reel' : 'Instagram Post')}" 
                 class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
          ` : ''}
          <div class="ig-placeholder-fallback ${pThumb ? 'hidden' : ''} w-full h-full bg-gradient-to-tr from-purple-900/40 via-pink-900/30 to-amber-900/40 flex flex-col items-center justify-center p-3 text-center border border-white/5">
            <div class="w-10 h-10 rounded-full bg-pink-500/20 flex items-center justify-center mb-2 border border-pink-500/30 shadow-inner">
              <i class="fa-solid ${isVideo ? 'fa-clapperboard text-pink-400' : 'fa-camera text-indigo-400'} text-base"></i>
            </div>
            <span class="text-[11px] font-mono font-bold text-gray-200">${isVideo ? 'Reel Video' : 'Photo Post'}</span>
            <span class="text-[9px] text-gray-400 mt-0.5 line-clamp-1">${pCap || '@' + username}</span>
          </div>

          <!-- Top Type Badge -->
          <div class="absolute top-2 left-2 z-10">
            ${isVideo ? `
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-pink-600/90 text-white font-semibold backdrop-blur-md shadow flex items-center gap-1 border border-pink-400/30">
                <i class="fa-solid fa-play text-[8px]"></i> Reel
              </span>
            ` : `
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-600/90 text-white font-semibold backdrop-blur-md shadow flex items-center gap-1 border border-indigo-400/30">
                <i class="fa-solid fa-image text-[8px]"></i> Post
              </span>
            `}
          </div>

          <!-- Bottom Metric Bar (Always Visible) -->
          <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-dark-950 via-dark-950/80 to-transparent p-2 pt-6 flex items-center justify-between text-xs font-mono font-bold text-white z-10">
            <span class="flex items-center gap-1 text-rose-400 drop-shadow"><i class="fa-solid fa-heart text-[10px]"></i> ${pLikes}</span>
            <span class="flex items-center gap-1 text-sky-400 drop-shadow"><i class="fa-solid fa-comment text-[10px]"></i> ${pComments}</span>
          </div>

          <!-- Full Hover Overlay with Caption -->
          <div class="absolute inset-0 bg-dark-950/90 opacity-0 group-hover:opacity-100 transition-opacity p-3 flex flex-col justify-between z-20">
            <span class="self-end text-[10px] font-mono px-1.5 py-0.5 rounded bg-pink-500/20 text-pink-300 border border-pink-500/30 flex items-center gap-1">
              <span>Open on IG</span> <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
            </span>
            <div class="space-y-1.5">
              <div class="flex items-center gap-3 text-xs font-mono font-bold text-white">
                <span class="flex items-center gap-1 text-rose-400"><i class="fa-solid fa-heart text-[11px]"></i> ${pLikes}</span>
                <span class="flex items-center gap-1 text-sky-400"><i class="fa-solid fa-comment text-[11px]"></i> ${pComments}</span>
              </div>
              ${pCap ? `<p class="text-[10px] text-gray-200 line-clamp-3 leading-relaxed">${pCap}</p>` : `<p class="text-[10px] text-gray-400 italic">No caption provided</p>`}
            </div>
          </div>
        </a>
      `;
    }).join('');

    mediaHtml = `
      <div class="space-y-3 pt-2">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
            <i class="fa-brands fa-instagram text-pink-400"></i>
            Recent Post Media &amp; Engagement Sample (${posts.length} posts)
          </h4>
          <span class="text-[11px] font-mono text-gray-500">Live Scraped Feed</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          ${postCards}
        </div>
      </div>
    `;
  } else {
    mediaHtml = `
      <div class="p-6 text-center text-xs text-gray-400 bg-dark-900/40 rounded-xl border border-white/5 space-y-1">
        <i class="fa-brands fa-instagram text-gray-500 text-lg mb-1 block"></i>
        <p class="font-medium text-gray-300">${isPrivate ? 'Account is Private' : 'No recent public media posts returned for this creator.'}</p>
        <p class="text-[11px] text-gray-500">Metrics are calculated from creator profile summary benchmarks.</p>
      </div>
    `;
  }

  // Method explanation
  let methodNote = 'Exact post metrics arithmetic across recent posts';
  if (erMethod === 'follower_tier_benchmark') {
    methodNote = 'Computed via follower-tier regression benchmark model with deterministic seed';
  } else if (erMethod === 'synthetic') {
    methodNote = 'Retrieved from local ADBMS benchmark synthetic database';
  } else if (erMethod === 'private_account') {
    methodNote = 'Account is private; post engagement data is hidden by Instagram';
  }

  cardEl.innerHTML = `
    <!-- Top Profile Glass Card -->
    <div class="glass-panel p-6 space-y-6 border border-pink-500/20 bg-gradient-to-b from-dark-900/90 to-dark-950/80">
      
      <!-- Card Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/5">
        <div class="flex items-center gap-4">
          <div class="relative">
            <img src="${avatarUrl}" 
                 data-orig-src="${avatarUrl}" 
                 referrerpolicy="no-referrer" 
                 onerror="if (!this.dataset.proxied && this.dataset.origSrc && this.dataset.origSrc.startsWith('http') && !this.dataset.origSrc.includes('ui-avatars')) { this.dataset.proxied = '1'; this.src = '/api/instagram/proxy-image?url=' + encodeURIComponent(this.dataset.origSrc); } else { this.onerror=null; this.src='${fallbackAvatar}'; }" 
                 alt="${fullName}" 
                 class="w-20 h-20 rounded-full object-cover border-2 border-pink-500/60 ig-ring-glow">
            ${isVerified ? '<div class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-dark-900 flex items-center justify-center border border-white/20 shadow-md"><i class="fa-solid fa-circle-check text-sky-400 text-sm"></i></div>' : ''}
          </div>
          <div class="space-y-1">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-xl font-bold text-white tracking-tight">${fullName}</h3>
              <span class="text-sm font-mono text-pink-400 font-semibold">@${username}</span>
              ${isPrivate ? '<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-white/10"><i class="fa-solid fa-lock text-[9px]"></i> Private</span>' : '<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><i class="fa-solid fa-globe text-[9px]"></i> Public</span>'}
            </div>
            <p class="text-xs text-gray-300 max-w-xl leading-relaxed whitespace-pre-line">${bio}</p>
          </div>
        </div>

        <!-- Badges & Action Controls -->
        <div class="flex flex-row md:flex-col items-end gap-2 shrink-0">
          ${cacheBadgeHtml}
          <div class="flex items-center gap-2 pt-1">
            <button onclick="searchInstagram('${username}', true)" title="Bypass MongoDB cache and force live re-scrape" class="py-1.5 px-3 rounded-lg text-xs bg-dark-800 hover:bg-dark-700 text-gray-300 hover:text-white border border-white/10 flex items-center gap-1.5 transition-all">
              <i class="fa-solid fa-arrows-rotate text-[11px] text-pink-400"></i>
              <span>Force Live Refresh</span>
            </button>
            <a href="https://instagram.com/${username}" target="_blank" rel="noopener noreferrer" class="py-1.5 px-3 rounded-lg text-xs bg-pink-950/40 hover:bg-pink-900/40 text-pink-300 border border-pink-500/30 flex items-center gap-1.5 transition-all">
              <i class="fa-brands fa-instagram text-xs"></i>
              <span>Open Profile ↗</span>
            </a>
          </div>
        </div>
      </div>

      <!-- Triple KPI Bar -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="glass-panel p-4 bg-dark-950/60 border border-white/5 space-y-1">
          <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">Followers</span>
          <div class="flex items-baseline justify-between">
            <span class="text-2xl font-extrabold text-white font-mono">${formatCompactNumber(followers)}</span>
            <span class="text-[11px] font-mono text-gray-500">${followers.toLocaleString()}</span>
          </div>
          <p class="text-[10px] text-gray-500">Global Audience Reach</p>
        </div>

        <div class="glass-panel p-4 bg-dark-950/60 border border-white/5 space-y-1">
          <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">Following</span>
          <div class="flex items-baseline justify-between">
            <span class="text-2xl font-extrabold text-white font-mono">${formatCompactNumber(following)}</span>
            <span class="text-[11px] font-mono text-gray-500">${following.toLocaleString()}</span>
          </div>
          <p class="text-[10px] text-gray-500">Accounts Followed</p>
        </div>

        <div class="glass-panel p-4 bg-dark-950/60 border border-white/5 space-y-1">
          <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">Total Posts</span>
          <div class="flex items-baseline justify-between">
            <span class="text-2xl font-extrabold text-white font-mono">${formatCompactNumber(postsCount)}</span>
            <span class="text-[11px] font-mono text-gray-500">${postsCount.toLocaleString()}</span>
          </div>
          <p class="text-[10px] text-gray-500">Published Media</p>
        </div>
      </div>

      <!-- Explicit Engagement Rate Breakdown Box -->
      <div class="er-formula-box p-5 rounded-2xl space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg">
              <i class="fa-solid fa-chart-line"></i>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-sm font-bold text-white">Calculated Engagement Rate (ER)</h4>
                ${erBadge}
              </div>
              <p class="text-[11px] text-gray-400">Core ADBMS analytic metric computed from interaction volume over audience size.</p>
            </div>
          </div>
          <div class="text-right">
            <span class="text-3xl font-extrabold text-emerald-400 font-mono tracking-tight">${er.toFixed(2)}%</span>
          </div>
        </div>

        <!-- Formula Display Card -->
        <div class="p-3.5 rounded-xl bg-dark-950/80 border border-white/10 space-y-2 text-xs font-mono">
          <div class="flex items-center justify-between text-gray-400 text-[11px] border-b border-white/5 pb-1.5">
            <span>MATHEMATICAL FORMULA:</span>
            <span class="text-indigo-400">ER = (avg_likes + avg_comments) / followers * 100</span>
          </div>
          <div class="text-gray-200 text-xs sm:text-sm pt-1 overflow-x-auto whitespace-nowrap">
            ER = (<span class="text-rose-400 font-bold">${avgLikes.toLocaleString()}</span> [avg likes] + <span class="text-sky-400 font-bold">${avgComments.toLocaleString()}</span> [avg comments]) / <span class="text-purple-400 font-bold">${followers.toLocaleString()}</span> [followers] &times; 100 = <span class="text-emerald-400 font-bold">${er.toFixed(2)}%</span>
          </div>
          <div class="text-[10px] text-gray-500 pt-1 flex items-center justify-between">
            <span>Method: ${methodNote}</span>
            <span class="text-gray-400">Avg Interactions/Post: ${(avgLikes + avgComments).toLocaleString()}</span>
          </div>
        </div>
      </div>

      <!-- Recent Media Posts Grid -->
      ${mediaHtml}

      <!-- Bottom Card Action Footer -->
      <div class="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-white/5 text-xs text-gray-400">
        <span class="flex items-center gap-1.5 font-mono text-[11px]">
          <i class="fa-solid fa-database text-emerald-400"></i>
          Stored in MongoDB <span class="text-indigo-300 font-bold">instagram_profiles</span> &amp; <span class="text-indigo-300 font-bold">influencers</span>
        </span>
        <div class="flex items-center gap-2">
          <button onclick="switchView('influencers'); document.getElementById('inf-search').value='@${username}'; loadInfluencers();" class="py-2 px-3.5 rounded-lg bg-dark-800 hover:bg-dark-700 text-gray-200 border border-white/10 flex items-center gap-1.5 transition-all">
            <i class="fa-solid fa-magnifying-glass text-xs"></i>
            <span>Search in Discovery Grid</span>
          </button>
        </div>
      </div>

    </div>
  `;

  cardEl.classList.remove('hidden');
}

function renderInstagramError(errorMessage, username) {
  window._currentFailedIgUser = username;

  const initialEl = document.getElementById('ig-initial-state');
  const skeletonEl = document.getElementById('ig-loading-skeleton');
  const cardEl = document.getElementById('ig-profile-card');
  const errorEl = document.getElementById('ig-error-fallback');
  const msgEl = document.getElementById('ig-error-message');
  const btnTextEl = document.getElementById('ig-fallback-btn-text');

  if (initialEl) initialEl.classList.add('hidden');
  if (skeletonEl) skeletonEl.classList.add('hidden');
  if (cardEl) cardEl.classList.add('hidden');

  if (msgEl) {
    msgEl.innerText = errorMessage || `Unable to reach Instagram API for @${username}.`;
  }
  if (btnTextEl) {
    btnTextEl.innerText = `Search Local Synthetic Database for "${username}"`;
  }
  if (errorEl) {
    errorEl.classList.remove('hidden');
  }
  showToast(`Instagram lookup notice: ${errorMessage}`, 'warning');
}

function fallbackToSynthetic(user) {
  const targetUser = user || window._currentFailedIgUser || '';
  switchView('influencers');
  const input = document.getElementById('inf-search');
  if (input) {
    input.value = targetUser.startsWith('@') ? targetUser : `@${targetUser}`;
  }
  loadInfluencers();
  showToast(`Redirected to synthetic database for ${targetUser}`, 'info');
}

/* ==========================================================================
   Instagram API Key Configuration Modal Controller
   ========================================================================== */

function openApiSettingsModal() {
  loadInstagramConfig();
  openModal('modal-api-settings');
}

async function loadInstagramConfig() {
  const modeEl = document.getElementById('settings-current-mode');
  const statusEl = document.getElementById('settings-key-status');

  try {
    const res = await fetch('/api/instagram/config');
    if (res.ok) {
      const cfg = await res.json();
      if (modeEl) {
        modeEl.innerText = cfg.active_mode === 'rapidapi' ? 'RapidAPI Live Scraper' : 'Direct Public Crawler Scraper';
      }
      if (statusEl) {
        statusEl.innerText = cfg.has_api_key ? (cfg.api_key_masked || 'Configured') : 'None (Auto Crawler)';
      }
    }
  } catch (e) {
    if (modeEl) modeEl.innerText = 'Direct Public Crawler';
    if (statusEl) statusEl.innerText = 'Unconfigured';
  }
}

async function handleSaveApiSettings(e) {
  e.preventDefault();
  const input = document.getElementById('settings-rapidapi-key');
  const apiKey = input ? input.value.trim() : '';

  try {
    const res = await fetch('/api/instagram/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey || null })
    });

    if (res.ok) {
      const resp = await res.json();
      showToast('Instagram API configuration saved', 'success');
      closeModal('modal-api-settings');
      loadInstagramConfig();
    } else {
      showToast('Failed to save API configuration', 'error');
    }
  } catch (err) {
    showToast(`Error saving configuration: ${err.message}`, 'error');
  }
}

function togglePasswordVisibility(inputId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById('eye-icon-settings');
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    if (icon) {
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    }
  } else {
    input.type = 'password';
    if (icon) {
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  }
}

