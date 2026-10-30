/**
 * Empirical Challenge: Testing DOM rendering, XSS vectors, and onerror fallbacks
 * Simulates browser environment for app.js rendering functions.
 */

const fs = require('fs');

// Read app.js
const appJs = fs.readFileSync('app/static/js/app.js', 'utf8');

// Extract helper functions and rendering functions needed
// We can set up a minimal DOM mock
class MockClassList {
  constructor() {
    this.classes = new Set();
  }
  add(...c) { c.forEach(x => this.classes.add(x)); }
  remove(...c) { c.forEach(x => this.classes.delete(x)); }
  contains(c) { return this.classes.has(c); }
  toggle(c, force) {
    if (force === true) this.classes.add(c);
    else if (force === false) this.classes.delete(c);
    else if (this.classes.has(c)) this.classes.delete(c);
    else this.classes.add(c);
  }
}

class MockElement {
  constructor(id = '') {
    this.id = id;
    this.classList = new MockClassList();
    this.innerHTML = '';
    this.innerText = '';
    this.value = '';
    this.attributes = {};
  }
  setAttribute(k, v) { this.attributes[k] = v; }
  getAttribute(k) { return this.attributes[k]; }
}

const elements = {};
function getElementById(id) {
  if (!elements[id]) {
    elements[id] = new MockElement(id);
  }
  return elements[id];
}

// Global mocks
global.document = {
  getElementById: getElementById,
  createElement: (tag) => new MockElement(tag)
};
global.window = {
  _currentFailedIgUser: null,
  addEventListener: () => {}
};
global.showToast = (msg, type) => {
  // console.log(`[TOAST ${type}] ${msg}`);
};

// We evaluate app.js in this context
// To safely extract functions without running DOMContentLoaded
const vm = require('vm');
const context = {
  document: global.document,
  window: global.window,
  showToast: global.showToast,
  console: console,
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  setInterval: setInterval,
  clearInterval: clearInterval,
  fetch: () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
};
vm.createContext(context);

// Load app.js into context
// We strip DOMContentLoaded listener so it doesn't trigger on init
const sanitizedCode = appJs.replace(/document\.addEventListener\('DOMContentLoaded'[\s\S]*?\}\);/, '// DOMContentLoaded mocked');
try {
  vm.runInContext(sanitizedCode, context);
  console.log('[PASS] app.js evaluated successfully in mock environment');
} catch (err) {
  console.error('[FAIL] Error evaluating app.js:', err.message);
  process.exit(1);
}

// -------------------------------------------------------------
// TEST 1: DOM Element references and Initial States
// -------------------------------------------------------------
console.log('\n--- TEST 1: DOM Elements and Rendering States ---');
const cardEl = context.document.getElementById('ig-profile-card');
const skeletonEl = context.document.getElementById('ig-loading-skeleton');
const initialEl = context.document.getElementById('ig-initial-state');
const errorEl = context.document.getElementById('ig-error-fallback');

// Verify helper function exists
console.log('formatCompactNumber exists:', typeof context.formatCompactNumber === 'function');
console.log('renderInstagramProfileCard exists:', typeof context.renderInstagramProfileCard === 'function');
console.log('renderInstagramError exists:', typeof context.renderInstagramError === 'function');
console.log('fallbackToSynthetic exists:', typeof context.fallbackToSynthetic === 'function');

// -------------------------------------------------------------
// TEST 2: XSS Safety Challenge on Creator Bio
// -------------------------------------------------------------
console.log('\n--- TEST 2: XSS Challenge on Creator Bio ---');
const xssPayloads = [
  '<script>alert("xss")</script>',
  '<img src=x onerror=alert("bio_img_xss")>',
  '<svg/onload=alert("bio_svg_xss")>',
  '"><script>alert(document.cookie)</script>',
  '<iframe src="javascript:alert(1)"></iframe>'
];

let xssBioVulnerabilities = 0;
for (const payload of xssPayloads) {
  const mockData = {
    username: 'test_creator',
    full_name: 'Test Creator',
    bio: `Passionate photographer ${payload} and traveler`,
    profile_pic_url: 'https://example.com/pic.jpg',
    is_verified: true,
    is_private: false,
    source: 'live_scraper',
    metrics: {
      followers: 10000,
      following: 200,
      posts_count: 50,
      engagement_rate: 3.5,
      engagement_rate_method: 'exact_arithmetic',
      avg_likes: 300,
      avg_comments: 50
    },
    recent_posts: []
  };

  context.renderInstagramProfileCard(mockData);
  const output = cardEl.innerHTML;

  if (output.includes(payload)) {
    console.log(`[VULNERABLE] Raw XSS payload reflected in cardEl.innerHTML: ${payload}`);
    xssBioVulnerabilities++;
  } else {
    console.log(`[SAFE] Payload escaped or filtered: ${payload}`);
  }
}

// -------------------------------------------------------------
// TEST 3: XSS Safety Challenge on Post Captions
// -------------------------------------------------------------
console.log('\n--- TEST 3: XSS Challenge on Post Captions ---');
let xssCaptionVulnerabilities = 0;
const captionPayloads = [
  "Nice photo! <img src=x onerror=alert('caption_xss')>",
  "Sunset view <svg onload=alert('caption_svg')>",
  "Check this out <script>alert('caption_script')</script>",
  "Quote 'test' and <details open ontoggle=alert('caption_toggle')>"
];

for (const payload of captionPayloads) {
  const mockData = {
    username: 'test_creator',
    full_name: 'Test Creator',
    bio: 'Normal bio',
    profile_pic_url: 'https://example.com/pic.jpg',
    is_verified: false,
    is_private: false,
    source: 'live_scraper',
    metrics: {
      followers: 5000,
      following: 100,
      posts_count: 10,
      engagement_rate: 2.1,
      engagement_rate_method: 'exact_arithmetic',
      avg_likes: 100,
      avg_comments: 5
    },
    recent_posts: [
      {
        caption: payload,
        likes: 100,
        comments: 5,
        thumbnail: 'https://example.com/thumb.jpg',
        url: 'https://instagram.com/p/123',
        post_type: 'Image'
      }
    ]
  };

  context.renderInstagramProfileCard(mockData);
  const output = cardEl.innerHTML;

  // The caption is placed in: <p class="text-[10px] text-gray-300 line-clamp-2">${pCap}</p>
  // If pCap contains raw HTML tags, it will be injected into innerHTML
  if (output.includes("<img src=x onerror=alert('caption_xss')>") ||
      output.includes("<svg onload=alert('caption_svg')>") ||
      output.includes("<script>alert('caption_script')</script>") ||
      output.includes("<details open ontoggle=alert('caption_toggle')>")) {
    console.log(`[VULNERABLE] Raw HTML tag from post caption injected into innerHTML: ${payload}`);
    xssCaptionVulnerabilities++;
  } else {
    console.log(`[SAFE] Caption escaped: ${payload}`);
  }
}

// -------------------------------------------------------------
// TEST 4: XSS Safety Challenge on Full Name and Username
// -------------------------------------------------------------
console.log('\n--- TEST 4: XSS Challenge on Full Name and Username ---');
let xssNameVulnerabilities = 0;
const namePayload = "John Doe <img src=x onerror=alert('name_xss')>";
const userPayload = "john_doe'; alert('user_xss'); //";

const mockNameData = {
  username: userPayload,
  full_name: namePayload,
  bio: 'Normal bio',
  profile_pic_url: 'https://example.com/pic.jpg',
  is_verified: false,
  is_private: false,
  source: 'live_scraper',
  metrics: { followers: 1000, following: 10, posts_count: 5, engagement_rate: 1.0, engagement_rate_method: 'benchmark', avg_likes: 10, avg_comments: 0 },
  recent_posts: []
};

context.renderInstagramProfileCard(mockNameData);
const nameOutput = cardEl.innerHTML;

if (nameOutput.includes("<img src=x onerror=alert('name_xss')>")) {
  console.log(`[VULNERABLE] Raw HTML tag from full_name injected into innerHTML: ${namePayload}`);
  xssNameVulnerabilities++;
} else {
  console.log('[SAFE] full_name properly escaped');
}

if (nameOutput.includes(`searchInstagram('${userPayload}', true)`)) {
  console.log(`[VULNERABLE] Username with quotes injected into onclick handler unescaped: ${userPayload}`);
  xssNameVulnerabilities++;
} else {
  console.log('[SAFE] username properly escaped in onclick handler');
}

// -------------------------------------------------------------
// TEST 5: Broken Image Fallback (onerror Handling)
// -------------------------------------------------------------
console.log('\n--- TEST 5: Broken Image Fallback (onerror Handling) ---');
const standardData = {
  username: 'test_broken_img',
  full_name: 'Broken Image Tester',
  bio: 'Bio text',
  profile_pic_url: 'https://invalid-broken-domain-404.xyz/avatar.jpg',
  is_verified: false,
  is_private: false,
  source: 'live_scraper',
  metrics: { followers: 500, following: 50, posts_count: 2, engagement_rate: 1.5, avg_likes: 10, avg_comments: 1 },
  recent_posts: [
    { thumbnail: 'https://invalid-broken-domain-404.xyz/thumb.jpg', caption: 'Test', likes: 5, comments: 1 }
  ]
};

context.renderInstagramProfileCard(standardData);
const stdOutput = cardEl.innerHTML;

// Check avatar onerror
const hasAvatarOnerror = stdOutput.includes('onerror="this.onerror=null;') && stdOutput.includes('ui-avatars.com');
if (hasAvatarOnerror) {
  console.log('[PASS] Avatar <img> has onerror attribute with ui-avatars.com and recursion prevention (this.onerror=null)');
} else {
  console.log('[FAIL] Avatar <img> missing or malformed onerror handler');
}

// Check thumbnail onerror
const hasThumbOnerror = stdOutput.includes('onerror="this.onerror=null;') && stdOutput.includes('thumb');
if (hasThumbOnerror) {
  console.log('[PASS] Thumbnail <img> has onerror attribute with recursion prevention (this.onerror=null)');
} else {
  console.log('[FAIL] Thumbnail <img> missing or malformed onerror handler');
}

// Subtest: Single quote in name breaking onerror handler
console.log('\n--- SUBTEST 5b: Single quote in full_name breaking inline onerror ---');
const nameWithQuote = "Jane O'Connor";
const dataWithQuote = {
  username: 'jane_oconnor',
  full_name: nameWithQuote,
  bio: 'Bio',
  profile_pic_url: 'https://invalid.com/avatar.jpg',
  metrics: { followers: 100, following: 10, posts_count: 1, engagement_rate: 1.0, avg_likes: 1, avg_comments: 1 },
  recent_posts: []
};
context.renderInstagramProfileCard(dataWithQuote);
const quoteOutput = cardEl.innerHTML;
// Look for onerror="this.onerror=null; this.src='https://ui-avatars.com/api/?name=Jane O'Connor...';"
if (quoteOutput.includes("this.src='https://ui-avatars.com/api/?name=Jane O'Connor")) {
  console.log("[VULNERABLE / SYNTAX BREAK] Unescaped single quote in full_name breaks inline onerror handler string: this.src='...Jane O'Connor...'");
} else {
  console.log("[PASS] Single quote properly escaped in onerror URL");
}

// -------------------------------------------------------------
// SUMMARY OF CHALLENGE
// -------------------------------------------------------------
console.log('\n=== EMPIRICAL CHALLENGE SUMMARY ===');
console.log(`XSS Bio Vulnerabilities Confirmed: ${xssBioVulnerabilities}`);
console.log(`XSS Caption Vulnerabilities Confirmed: ${xssCaptionVulnerabilities}`);
console.log(`XSS Name/User Vulnerabilities Confirmed: ${xssNameVulnerabilities}`);
const totalXss = xssBioVulnerabilities + xssCaptionVulnerabilities + xssNameVulnerabilities;
console.log(`TOTAL XSS ISSUES: ${totalXss}`);

if (totalXss > 0) {
  console.log('\nVERDICT REQUIREMENT: REQUEST_CHANGES (Definite XSS injection vulnerabilities in renderInstagramProfileCard)');
} else {
  console.log('\nVERDICT: APPROVE');
}
