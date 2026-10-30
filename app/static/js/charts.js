/**
 * SocialPulse Charts Manager
 * Chart.js configurations and helpers for dark-mode glassmorphism analytics
 */

const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

/**
 * Overview: Trend Velocity Bar Chart
 */
function renderTrendVelocityChart(canvasId, trends) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = trends.map(t => t.hashtag);
  const data = trends.map(t => t.velocity_score);

  const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, 'rgba(99, 102, 241, 0.85)');
  gradient.addColorStop(1, 'rgba(139, 92, 246, 0.15)');

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Velocity Score (Pts)',
        data: data,
        backgroundColor: gradient,
        borderColor: '#6366f1',
        borderWidth: 1.5,
        borderRadius: 6,
        maxBarThickness: 45
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#fff',
          bodyColor: '#e5e7eb',
          borderColor: 'rgba(99, 102, 241, 0.4)',
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          callbacks: {
            label: (ctx) => ` Velocity: ${ctx.parsed.y} pts/hr`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af', font: { size: 10, family: 'Inter' } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af', font: { size: 10, family: 'Inter' } }
        }
      }
    }
  });
}

/**
 * Overview: Platform Distribution Doughnut Chart
 */
function renderPlatformDistributionChart(canvasId, platformData) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const platformColors = {
    'Instagram': '#ec4899',
    'YouTube': '#ef4444',
    'TikTok': '#06b6d4',
    'Twitter/X': '#3b82f6',
    'LinkedIn': '#6366f1'
  };

  const labels = platformData.map(p => p._id);
  const counts = platformData.map(p => p.count);
  const backgroundColors = labels.map(l => platformColors[l] || '#8b5cf6');

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: backgroundColors,
        borderWidth: 2,
        borderColor: '#111827',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#fff',
          bodyColor: '#e5e7eb',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 8
        }
      }
    }
  });

  // Render Legend HTML
  const legendContainer = document.getElementById('platform-legend-container');
  if (legendContainer) {
    legendContainer.innerHTML = platformData.map((item, idx) => `
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${backgroundColors[idx]}"></span>
        <span class="text-gray-300">${item._id}:</span>
        <span class="font-mono text-white font-bold ml-auto">${item.count}</span>
      </div>
    `).join('');
  }
}

/**
 * Creator Detail: Demographics Age Breakdown Bar Chart
 */
function renderAgeDemographicsChart(canvasId, ageBrackets) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = Object.keys(ageBrackets);
  const values = Object.values(ageBrackets);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Audience Share %',
        data: values,
        backgroundColor: 'rgba(99, 102, 241, 0.65)',
        borderColor: '#818cf8',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.y}% of audience`
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } },
        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 10 } } }
      }
    }
  });
}

/**
 * Creator Detail: Content Type Breakdown Doughnut
 */
function renderContentTypeChart(canvasId, contentBreakdown) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = contentBreakdown.map(c => c._id || 'Standard');
  const values = contentBreakdown.map(c => c.count);

  const colors = ['#6366f1', '#ec4899', '#06b6d4', '#10b981', '#f59e0b'];

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 2,
        borderColor: '#111827'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9ca3af', boxWidth: 12, font: { size: 10 } } }
      }
    }
  });
}

/**
 * Trend Detail: 24-Hour Hourly Progression Line Chart
 */
function renderTrendHourlyProgressionChart(canvasId, hourlyData) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = hourlyData.map(h => h.hour);
  const values = hourlyData.map(h => h.volume);

  const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 250);
  gradient.addColorStop(0, 'rgba(6, 182, 212, 0.4)');
  gradient.addColorStop(1, 'rgba(6, 182, 212, 0.0)');

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Hourly Post Volume',
        data: values,
        borderColor: '#06b6d4',
        borderWidth: 2.5,
        backgroundColor: gradient,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#06b6d4',
        pointRadius: 2,
        pointHoverRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#fff',
          bodyColor: '#e5e7eb',
          borderColor: 'rgba(6, 182, 212, 0.4)',
          borderWidth: 1,
          padding: 8,
          callbacks: {
            label: (ctx) => ` Volume: ${ctx.parsed.y.toLocaleString()} posts`
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 }, maxTicksLimit: 12 } },
        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af', font: { size: 9 } } }
      }
    }
  });
}

/**
 * Head-to-Head Creator Comparison Radar Chart
 */
function renderComparisonRadarChart(canvasId, influencers) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const colors = [
    { border: '#6366f1', bg: 'rgba(99, 102, 241, 0.25)' },
    { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.25)' },
    { border: '#06b6d4', bg: 'rgba(6, 182, 212, 0.25)' },
    { border: '#10b981', bg: 'rgba(16, 185, 129, 0.25)' }
  ];

  // Normalized dimensions (0 to 100)
  const datasets = influencers.map((infItem, idx) => {
    const inf = infItem.influencer;
    const color = colors[idx % colors.length];

    // Normalize values
    const normFollowers = Math.min(100, Math.round((inf.metrics.followers_count / 3000000) * 100));
    const normER = Math.min(100, Math.round((inf.metrics.engagement_rate / 12) * 100));
    const normCred = inf.metrics.credibility_score;
    const normAuthenticity = Math.max(0, Math.round(100 - (inf.metrics.fake_followers_pct * 8)));
    const normAvgLikes = Math.min(100, Math.round((inf.metrics.avg_likes / 150000) * 100));

    return {
      label: inf.name,
      data: [normFollowers, normER, normCred, normAuthenticity, normAvgLikes],
      borderColor: color.border,
      backgroundColor: color.bg,
      borderWidth: 2,
      pointBackgroundColor: color.border,
      pointRadius: 3
    };
  });

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Audience Reach', 'Engagement Rate', 'Credibility Score', 'Authenticity', 'Avg Post Likes'],
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
          grid: { color: 'rgba(255, 255, 255, 0.08)' },
          pointLabels: { color: '#d1d5db', font: { size: 10, family: 'Inter' } },
          ticks: { display: false, max: 100, min: 0 }
        }
      },
      plugins: {
        legend: { position: 'top', labels: { color: '#f3f4f6', boxWidth: 12, font: { size: 11 } } }
      }
    }
  });
}

/**
 * Single Creator Demographics & Performance Radar Chart
 */
function renderCreatorDemographicsRadar(canvasId, influencer) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const inf = influencer;
  const m = inf.metrics || {};
  const demo = inf.audience_demographics || {};
  const age = demo.age_brackets || {};

  const reachScore = Math.min(100, Math.round(((m.followers_count || 0) / 2500000) * 100));
  const erScore = Math.min(100, Math.round(((m.engagement_rate || 0) / 10) * 100));
  const credScore = m.credibility_score || 85;
  const authenticity = Math.max(0, Math.round(100 - ((m.fake_followers_pct || 5) * 8)));
  const coreDemo = Math.min(100, Math.round((age['18-24'] || 30) + (age['25-34'] || 40)));

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Audience Reach', 'Engagement Rate', 'Credibility Score', 'Authenticity', 'Core 18-34 Demo'],
      datasets: [{
        label: inf.name || inf.handle,
        data: [reachScore, erScore, credScore, authenticity, coreDemo],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.25)',
        borderWidth: 2,
        pointBackgroundColor: '#818cf8',
        pointRadius: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
          grid: { color: 'rgba(255, 255, 255, 0.08)' },
          pointLabels: { color: '#d1d5db', font: { size: 8.5, family: 'Inter' } },
          ticks: { display: false, max: 100, min: 0 }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}
