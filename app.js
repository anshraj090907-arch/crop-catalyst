// ════════════════════════════════════════════════════════════
//  Crop Catalyst — Frontend Logic
//  Talks to Flask backend at http://localhost:5000
// ════════════════════════════════════════════════════════════

const BACKEND = 'http://localhost:5000';

// ── Crop data (for guide + overview) ─────────────────────────
const CROP_DATA = {
  Wheat:   { emoji:'🌾', season:'Oct – Mar', water:'450–650 mm', temp:'15–25°C', harvest:'120–150 days' },
  Rice:    { emoji:'🍚', season:'Jun – Nov', water:'1200–2000 mm', temp:'20–35°C', harvest:'90–150 days' },
  Maize:   { emoji:'🌽', season:'Jun – Oct', water:'500–800 mm', temp:'18–27°C', harvest:'60–100 days' },
  Cotton:  { emoji:'🌿', season:'Apr – Nov', water:'700–1300 mm', temp:'21–35°C', harvest:'150–180 days' },
  Barley:  { emoji:'🌾', season:'Oct – Apr', water:'400–600 mm', temp:'12–25°C', harvest:'90–120 days' },
  Soybean: { emoji:'🫘', season:'Jun – Oct', water:'450–700 mm', temp:'20–30°C', harvest:'90–120 days' },
};

// ── DOM refs ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Sliders live-update labels ────────────────────────────────
$('rainfall').addEventListener('input',      e => $('rainfall-val').textContent = e.target.value);
$('temperature').addEventListener('input',   e => $('temp-val').textContent     = e.target.value);
$('days_to_harvest').addEventListener('input',e=> $('days-val').textContent    = e.target.value);

// ── Toggle labels ─────────────────────────────────────────────
$('fertilizer').addEventListener('change', e => {
  $('fert-state').textContent = e.target.checked ? 'Yes' : 'No';
});
$('irrigation').addEventListener('change', e => {
  $('irr-state').textContent = e.target.checked ? 'Yes' : 'No';
});

// ── Live summary update ───────────────────────────────────────
function updateSummary() {
  $('s-region').textContent  = $('region').value;
  $('s-crop').textContent    = $('crop').value;
  $('s-soil').textContent    = $('soil_type').value;
  $('s-weather').textContent = $('weather').value;
  $('s-rainfall').textContent= $('rainfall').value + ' mm';
  $('s-temp').textContent    = $('temperature').value + ' °C';
  $('s-days').textContent    = $('days_to_harvest').value;
  $('s-fert').textContent    = $('fertilizer').checked ? 'Yes' : 'No';
  $('s-irr').textContent     = $('irrigation').checked ? 'Yes' : 'No';
}

['region','crop','soil_type','weather','rainfall','temperature',
 'days_to_harvest','fertilizer','irrigation'].forEach(id => {
  $( id ).addEventListener('change', updateSummary);
  $( id ).addEventListener('input',  updateSummary);
});
updateSummary();

// ── Check backend health ──────────────────────────────────────
async function checkHealth() {
  const dot  = $('status-dot');
  const text = $('status-text');
  try {
    const res = await fetch(`${BACKEND}/health`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      dot.className  = 'status-dot connected';
      text.textContent = 'Backend connected ✓';
    } else throw new Error();
  } catch {
    dot.className  = 'status-dot error';
    text.textContent = 'Backend offline';
  }
}
checkHealth();

// ── Show / hide helpers ───────────────────────────────────────
function show(id)  { $(id).classList.remove('hidden'); }
function hide(id)  { $(id).classList.add('hidden'); }

// ── Animated number counter ───────────────────────────────────
function animateNumber(el, target, decimals = 2, durationMs = 1200) {
  const start     = performance.now();
  const startVal  = 0;
  function step(now) {
    const t       = Math.min((now - start) / durationMs, 1);
    const eased   = 1 - Math.pow(1 - t, 3);          // ease-out-cubic
    const current = startVal + (target - startVal) * eased;
    el.textContent = current.toFixed(decimals);
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = target.toFixed(decimals);
  }
  requestAnimationFrame(step);
}

// ── Ring chart update ─────────────────────────────────────────
function setRing(fraction) {
  const circumference = 2 * Math.PI * 50;           // r = 50 → C ≈ 314
  const offset        = circumference * (1 - Math.min(fraction, 1));
  const ring          = $('ring-fill');

  // Inject SVG gradient once
  if (!document.getElementById('ringGradient')) {
    const svg  = ring.closest('svg');
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%"   stop-color="#4ade80" />
        <stop offset="100%" stop-color="#22c55e" />
      </linearGradient>`;
    svg.insertBefore(defs, svg.firstChild);
    ring.setAttribute('stroke', 'url(#ringGradient)');
  }

  ring.style.strokeDasharray  = circumference;
  ring.style.strokeDashoffset = circumference;    // start at 0

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      ring.style.strokeDashoffset = offset;
    });
  });
}

// ── Yield grade label ─────────────────────────────────────────
function getGrade(val) {
  if (val >= 7)   return { label:'🏆 Excellent',  cls:'grade-excellent' };
  if (val >= 5)   return { label:'👍 Good',        cls:'grade-good'      };
  if (val >= 3)   return { label:'📊 Moderate',    cls:'grade-moderate'  };
  if (val >= 1.5) return { label:'⚠️ Below Avg',   cls:'grade-low'       };
  return           { label:'🚨 Very Low',          cls:'grade-poor'      };
}

// ── Render suggestions & tips ─────────────────────────────────
function renderSuggestions(suggestions, tips) {
  const sl = $('sugg-list');
  const tl = $('tips-list');
  sl.innerHTML = '';
  tl.innerHTML = '';

  if (suggestions.length) {
    suggestions.forEach((s, i) => {
      const div = document.createElement('div');
      div.className = 'sugg-item';
      div.style.animationDelay = `${i * 0.08}s`;
      div.textContent = s;
      sl.appendChild(div);
    });
  } else {
    sl.innerHTML = '<p style="color:var(--text-muted);font-size:13px">No immediate actions needed.</p>';
  }

  if (tips.length) {
    tips.forEach((t, i) => {
      const div = document.createElement('div');
      div.className = 'tip-item';
      div.style.animationDelay = `${i * 0.08}s`;
      div.textContent = t;
      tl.appendChild(div);
    });
  } else {
    tl.innerHTML = '<p style="color:var(--text-muted);font-size:13px">No tips available.</p>';
  }

  show('suggestions-section');
}

// ── Render crop guide ─────────────────────────────────────────
function renderCropGuide(cropName) {
  const guide = CROP_DATA[cropName];
  if (!guide) return;

  $('crop-guide-title').textContent = `${guide.emoji} ${cropName} — Complete Farming Reference`;

  const entries = [
    { icon:'📅', label:'Growing Season', value: guide.season    },
    { icon:'💧', label:'Water Needs',    value: guide.water     },
    { icon:'🌡', label:'Ideal Temp',     value: guide.temp      },
    { icon:'⏱', label:'Days to Harvest', value: guide.harvest   },
  ];

  const grid = $('guide-grid');
  grid.innerHTML = entries.map((e,i) => `
    <div class="guide-card" style="animation-delay:${i*0.1}s">
      <div class="g-icon">${e.icon}</div>
      <div class="g-label">${e.label}</div>
      <div class="g-value">${e.value}</div>
    </div>
  `).join('');

  show('crop-guide-section');
}

// ── Render all-crops overview ─────────────────────────────────
function renderCropsOverview() {
  const grid = $('crops-overview');
  grid.innerHTML = Object.entries(CROP_DATA).map(([name, d]) => `
    <div class="crop-card" onclick="selectCrop('${name}')" id="crop-card-${name}" title="Click to select ${name}">
      <span class="crop-emoji">${d.emoji}</span>
      <div class="crop-name">${name}</div>
      <div class="crop-season">${d.season}</div>
    </div>
  `).join('');
}
renderCropsOverview();

function selectCrop(name) {
  $('crop').value = name;
  updateSummary();
  // Highlight selected
  document.querySelectorAll('.crop-card').forEach(c => c.style.borderColor = '');
  const card = $(`crop-card-${name}`);
  if (card) {
    card.style.borderColor = 'var(--green-400)';
    card.style.boxShadow   = '0 0 20px rgba(74,222,128,0.3)';
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Main predict function ─────────────────────────────────────
async function predict() {
  const btn = $('predict-btn');

  // Gather inputs
  const payload = {
    rainfall_mm:        Number($('rainfall').value),
    temperature_celsius:Number($('temperature').value),
    fertilizer_used:    $('fertilizer').checked,
    irrigation_used:    $('irrigation').checked,
    region:             $('region').value,
    crop_type:          $('crop').value,
    soil_type:          $('soil_type').value,
    weather_condition:  $('weather').value,
    days_to_harvest:    Number($('days_to_harvest').value)
  };

  // Update summary display
  updateSummary();

  // UI state: loading
  btn.disabled = true;
  btn.classList.add('loading');
  $('btn-text') && ($('btn-text').textContent = 'Predicting');
  hide('result-card');
  hide('error-card');
  hide('suggestions-section');
  hide('crop-guide-section');
  show('loading-card');

  try {
    const res = await fetch(`${BACKEND}/predict`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
      signal:  AbortSignal.timeout(15000)
    });

    const data = await res.json();
    hide('loading-card');

    if (data.error) {
      $('error-msg').textContent = '❌ ' + data.error;
      show('error-card');
      return;
    }

    // ── Show result ──────────────────────────────────────────
    const yieldVal = data.predicted_yield;
    const r2       = data.r2_score;

    show('result-card');

    // Animated yield number
    animateNumber($('yield-num'), yieldVal, 2, 1200);
    $('yield-label').textContent = `${yieldVal} tons/hectare`;
    $('r2-label').textContent    = (typeof r2 === 'number') ? r2.toFixed(4) : (r2 ?? 'N/A');

    // Ring (max ~10 t/ha = 100%)
    setRing(yieldVal / 10);

    // Progress bar
    setTimeout(() => {
      $('yield-bar').style.width = `${Math.min(yieldVal / 10 * 100, 100)}%`;
    }, 100);

    // Grade badge
    const grade = getGrade(yieldVal);
    const gDiv  = $('yield-grade');
    gDiv.textContent = grade.label;
    gDiv.className   = `yield-grade ${grade.cls}`;

    // Suggestions
    renderSuggestions(data.suggestions || [], data.tips || []);
    renderCropGuide(payload.crop_type);

    // Scroll to result
    $('result-card').scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Update health badge
    checkHealth();

  } catch (err) {
    hide('loading-card');
    $('error-msg').textContent = '🔌 Cannot connect to backend! Make sure backend.py is running on port 5000.';
    show('error-card');
  } finally {
    btn.disabled = false;
    btn.classList.remove('loading');
    const btnText = btn.querySelector('.btn-text');
    if (btnText) btnText.textContent = 'Predict Yield';
  }
}

// ── Enter key shortcut ────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.target.matches('select, input[type=range]')) {
    predict();
  }
});

// ── Periodic health check ─────────────────────────────────────
setInterval(checkHealth, 30000);
