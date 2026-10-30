/**
 * Empirical Challenge: Testing UI event handlers and state machines in app.js
 */

const fs = require('fs');
const vm = require('vm');

const appJs = fs.readFileSync('app/static/js/app.js', 'utf8');

// Build mock DOM elements
class MockElement {
  constructor(id = '', tagName = 'div') {
    this.id = id;
    this.tagName = tagName.toUpperCase();
    this.classList = {
      classes: new Set(),
      add(...c) { c.forEach(x => this.classes.add(x)); },
      remove(...c) { c.forEach(x => this.classes.delete(x)); },
      contains(c) { return this.classes.has(c); },
      toggle(c, f) {
        if (f === true) this.classes.add(c);
        else if (f === false) this.classes.delete(c);
        else if (this.classes.has(c)) this.classes.delete(c);
        else this.classes.add(c);
      }
    };
    this.innerHTML = '';
    this.innerText = '';
    this.value = '';
    this.type = 'text';
    this.listeners = {};
    this.children = [];
  }

  remove() {}

  appendChild(el) {
    this.children.push(el);
  }

  addEventListener(event, fn) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(fn);
  }

  trigger(event, data = {}) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(fn => fn(data));
    }
  }
}

const domStore = {};
function getOrCreate(id, tag = 'div') {
  if (!domStore[id]) {
    domStore[id] = new MockElement(id, tag);
  }
  return domStore[id];
}

// Pre-create required elements
const requiredIds = [
  'ig-search-input', 'ig-search-btn', 'ig-initial-state', 'ig-loading-skeleton',
  'ig-profile-card', 'ig-error-fallback', 'ig-error-message', 'ig-fallback-btn-text',
  'ig-skeleton-status', 'settings-current-mode', 'settings-key-status',
  'settings-rapidapi-key', 'eye-icon-settings', 'modal-api-settings',
  'inf-search', 'toast-container', 'global-search-input'
];

requiredIds.forEach(id => getOrCreate(id));

const toastsFired = [];
let fetchCallHistory = [];

const context = {
  document: {
    getElementById: (id) => domStore[id] || getOrCreate(id),
    createElement: (tag) => new MockElement('', tag),
    addEventListener: () => {}
  },
  window: {
    _currentFailedIgUser: null,
    addEventListener: () => {}
  },
  showToast: (msg, type) => {
    toastsFired.push({ msg, type });
  },
  console: console,
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  setInterval: setInterval,
  clearInterval: clearInterval,
  requestAnimationFrame: (cb) => { cb(); },
  fetch: (url, opts = {}) => {
    fetchCallHistory.push({ url, opts });
    if (url.includes('/api/instagram/profile/error_user')) {
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ error: 'User error_user not found' })
      });
    }
    if (url.includes('/api/instagram/profile/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          username: 'valid_user',
          full_name: 'Valid User',
          bio: 'Bio',
          profile_pic_url: 'https://pic.jpg',
          source: 'cached_instagram',
          metrics: { followers: 500, following: 10, posts_count: 5, engagement_rate: 2.0, avg_likes: 10, avg_comments: 0 }
        })
      });
    }
    if (url === '/api/instagram/config') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ has_api_key: true, api_key_masked: 'rap***123', active_mode: 'rapidapi' })
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  }
};

vm.createContext(context);
const sanitizedCode = appJs.replace(/document\.addEventListener\('DOMContentLoaded'[\s\S]*?\}\);/, '// mocked');
vm.runInContext(sanitizedCode, context);

// Mock external functions called by handlers
context.loadInfluencers = () => { context._loadInfluencersCalled = true; };

async function runTests() {
  console.log('=== EMPIRICAL UI EVENT HANDLERS TEST ===\n');

  // TEST 1: initInstagramLiveView and Enter key listener
  console.log('--- TEST 1: Enter Key Listener on Search Input ---');
  context.initInstagramLiveView();
  const searchInput = domStore['ig-search-input'];
  console.log('Search input has keydown listener:', Boolean(searchInput.listeners['keydown'] && searchInput.listeners['keydown'].length > 0));

  // Trigger Enter on search input with empty value
  searchInput.value = '';
  toastsFired.length = 0;
  searchInput.trigger('keydown', { key: 'Enter' });
  const emptyToast = toastsFired.find(t => t.msg.includes('Please enter an Instagram username'));
  console.log('Empty search triggers warning toast:', Boolean(emptyToast));

  // Trigger Enter with valid username
  searchInput.value = '@cristiano';
  fetchCallHistory.length = 0;
  searchInput.trigger('keydown', { key: 'Enter' });
  await new Promise(r => setTimeout(r, 50));
  const fetchedCristiano = fetchCallHistory.find(f => f.url.includes('/api/instagram/profile/cristiano'));
  console.log('Enter key on @cristiano initiates profile fetch without @:', Boolean(fetchedCristiano));

  // TEST 2: Demo Chips (fillAndSearchIg)
  console.log('\n--- TEST 2: One-Click Demo Chips (fillAndSearchIg) ---');
  fetchCallHistory.length = 0;
  context.fillAndSearchIg('therock');
  console.log('Input value updated to therock:', domStore['ig-search-input'].value === 'therock');
  await new Promise(r => setTimeout(r, 50));
  const fetchedRock = fetchCallHistory.find(f => f.url.includes('/api/instagram/profile/therock'));
  console.log('Chip fetch initiated for therock:', Boolean(fetchedRock));

  // TEST 3: State Transitions during Search (Skeleton -> Card)
  console.log('\n--- TEST 3: State Machine: Skeleton -> Profile Card ---');
  searchInput.value = 'valid_user';
  const skeleton = domStore['ig-loading-skeleton'];
  const card = domStore['ig-profile-card'];
  const error = domStore['ig-error-fallback'];

  const searchPromise = context.searchInstagram('valid_user');
  // While async running, skeleton should NOT have hidden
  console.log('During search: skeleton visible (!hidden):', !skeleton.classList.contains('hidden'));
  console.log('During search: card hidden:', card.classList.contains('hidden'));

  await searchPromise;
  console.log('After success: skeleton hidden:', skeleton.classList.contains('hidden'));
  console.log('After success: card visible (!hidden):', !card.classList.contains('hidden'));
  console.log('After success: error hidden:', error.classList.contains('hidden'));

  // TEST 4: Error State Transition and Fallback to Synthetic
  console.log('\n--- TEST 4: Error State Transition and Fallback ---');
  await context.searchInstagram('error_user');
  console.log('After error: skeleton hidden:', skeleton.classList.contains('hidden'));
  console.log('After error: card hidden:', card.classList.contains('hidden'));
  console.log('After error: error fallback visible (!hidden):', !error.classList.contains('hidden'));
  console.log('Error message text set:', domStore['ig-error-message'].innerText.includes('error_user not found'));
  console.log('Fallback button text updated:', domStore['ig-fallback-btn-text'].innerText.includes('error_user'));
  console.log('Failed user stored in window._currentFailedIgUser:', context.window._currentFailedIgUser === 'error_user');

  // TEST 5: Fallback redirection
  console.log('\n--- TEST 5: fallbackToSynthetic() Execution ---');
  context._loadInfluencersCalled = false;
  context.fallbackToSynthetic();
  console.log('inf-search input populated with @error_user:', domStore['inf-search'].value === '@error_user');
  console.log('loadInfluencers() triggered:', context._loadInfluencersCalled);

  // TEST 6: Password Visibility Toggle
  console.log('\n--- TEST 6: togglePasswordVisibility ---');
  const pwdInput = domStore['settings-rapidapi-key'];
  pwdInput.type = 'password';
  const eyeIcon = domStore['eye-icon-settings'];
  eyeIcon.classList.add('fa-eye');

  context.togglePasswordVisibility('settings-rapidapi-key');
  console.log('After toggle 1: input type is text:', pwdInput.type === 'text');
  console.log('After toggle 1: icon has fa-eye-slash:', eyeIcon.classList.contains('fa-eye-slash'));

  context.togglePasswordVisibility('settings-rapidapi-key');
  console.log('After toggle 2: input type is password:', pwdInput.type === 'password');
  console.log('After toggle 2: icon has fa-eye:', eyeIcon.classList.contains('fa-eye'));

  // TEST 7: Settings Modal save API Key
  console.log('\n--- TEST 7: handleSaveApiSettings ---');
  pwdInput.value = 'my-new-rapidapi-key';
  fetchCallHistory.length = 0;
  let prevented = false;
  await context.handleSaveApiSettings({ preventDefault: () => { prevented = true; } });
  console.log('Form submission prevented default:', prevented);
  const postConfig = fetchCallHistory.find(f => f.url === '/api/instagram/config' && f.opts.method === 'POST');
  console.log('POST /api/instagram/config sent with key:', Boolean(postConfig && JSON.parse(postConfig.opts.body).api_key === 'my-new-rapidapi-key'));

  console.log('\n=== ALL EVENT HANDLER TESTS FINISHED ===');
}

runTests();
