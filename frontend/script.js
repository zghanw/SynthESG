/**
 * SynthESG — Frontend Application
 *
 * Handles company ESG analysis via the API, renders research
 * insights, animated score visualizations, and source evidence.
 */

// ---------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------

const CONFIG = {
    // For local development: http://localhost:8000
    // For production: set window.SYNTHESG_API_ENDPOINT before loading this script
    API_ENDPOINT: window.SYNTHESG_API_ENDPOINT || 'http://localhost:8000',
};

let currentCompanyData = null;

// DOM helpers
const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------
// Quick Search
// ---------------------------------------------------------------

function quickSearch(company) {
    $('companyName').value = company;
    analyzeCompany();
}

// ---------------------------------------------------------------
// Main Analysis
// ---------------------------------------------------------------

async function analyzeCompany() {
    const companyInput = $('companyName').value.trim();
    if (!companyInput) {
        $('companyName').focus();
        return;
    }

    // Show loading
    showSection('loading');
    updateLoadingSteps(1);

    try {
        // Step 1: Validating
        await delay(400);
        updateLoadingSteps(2);
        $('loadingStatus').textContent = `Researching ESG data for "${companyInput}"…`;

        const response = await fetch(`${CONFIG.API_ENDPOINT}/api/v1/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_name: companyInput }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            if (err.error === 'company_not_found') {
                showError('Company Not Found', err.message, err.suggestion, 'danger');
                return;
            }
            throw new Error(err.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            showError('Analysis Error', data.message || data.error, data.suggestion, 'warning');
            return;
        }

        // Step 3: Scoring
        updateLoadingSteps(3);
        $('loadingStatus').textContent = 'Calculating scores…';
        await delay(300);

        currentCompanyData = data;
        displayResults(data);

    } catch (error) {
        console.error('Analysis failed:', error);
        showError('Connection Error', error.message, 'Check your connection and try again.', 'danger');
    }
}

// ---------------------------------------------------------------
// Display Results
// ---------------------------------------------------------------

function displayResults(data) {
    // Company info
    $('resultCompany').textContent = data.company_name;
    $('sectorBadge').innerHTML = `<i class="fas fa-industry"></i> ${data.sector || 'Unknown'}`;
    $('countryBadge').innerHTML = `<i class="fas fa-globe"></i> ${data.country || 'Global'}`;

    const ticker = data.ticker && data.ticker !== 'N/A' ? data.ticker : '';
    $('tickerBadge').textContent = ticker ? `$${ticker}` : '';
    $('tickerBadge').style.display = ticker ? 'inline-flex' : 'none';

    // Logo
    const logo = $('companyLogo');
    logo.src = data.company_logo || generateFallbackLogo(data.company_name);
    logo.onerror = () => { logo.src = generateFallbackLogo(data.company_name); };

    // Scores
    const esgScore = data.esg_score || 0;
    $('esgScore').textContent = esgScore;
    $('esgRating').textContent = data.rating || 'N/A';

    // Animate ring
    const circumference = 2 * Math.PI * 52;
    const offset = circumference - (esgScore / 100) * circumference;
    requestAnimationFrame(() => {
        $('ringFill').style.strokeDashoffset = offset;
    });

    // Pillar scores with animated bars
    const pillars = [
        { score: data.environmental, id: 'envScore', bar: 'envBar' },
        { score: data.social, id: 'socialScore', bar: 'socialBar' },
        { score: data.governance, id: 'govScore', bar: 'govBar' },
        { score: data.innovation, id: 'innovScore', bar: 'innovBar' },
    ];

    pillars.forEach((p) => {
        const score = p.score || 0;
        $(p.id).textContent = `${score}/25`;
        requestAnimationFrame(() => {
            $(p.bar).style.width = `${(score / 25) * 100}%`;
        });
    });

    // Research Insights
    renderInsights(data.research_insights || []);

    // News Evidence
    renderEvidence(data.news_evidence || []);

    // Risk Factors
    renderRisks(data.risk_factors || []);

    // Methodology
    if (data.methodology) {
        const parts = [data.methodology.framework];
        if (data.methodology.research_applied) {
            parts.push('Scores adjusted using real-time research data from web sources.');
        }
        parts.push(`Each ESG pillar scores up to ${data.methodology.max_pillar_score} points.`);
        $('methodologyText').textContent = parts.join(" - ");
    }

    showSection('results');
}

// ---------------------------------------------------------------
// Render Components
// ---------------------------------------------------------------

function renderInsights(insights) {
    const grid = $('insightsGrid');
    $('insightCount').textContent = `${insights.length} insight${insights.length !== 1 ? 's' : ''}`;

    if (!insights.length) {
        grid.innerHTML = '<p style="color: var(--text-muted); font-size: 14px;">No AI insights available for this company.</p>';
        return;
    }

    grid.innerHTML = insights.map(i => `
        <div class="insight-card">
            <div class="insight-category">${escapeHtml(i.category)}</div>
            <div class="insight-text">${escapeHtml(i.finding)}</div>
            <div class="insight-sources">${i.source_count} source${i.source_count !== 1 ? 's' : ''}</div>
        </div>
    `).join('');
}

function renderEvidence(evidence) {
    const list = $('evidenceList');
    $('evidenceCount').textContent = `${evidence.length} source${evidence.length !== 1 ? 's' : ''}`;

    if (!evidence.length) {
        list.innerHTML = '<p style="color: var(--text-muted); font-size: 14px; text-align: center; padding: 20px;">No source evidence available.</p>';
        return;
    }

    const categoryColors = {
        'Esg Overview': 'var(--accent)',
        'Environmental': 'var(--env-color)',
        'Social': 'var(--soc-color)',
        'Governance': 'var(--gov-color)',
        'Innovation': 'var(--inn-color)',
        'Risks': 'var(--risk-color)',
    };

    list.innerHTML = evidence.map(e => {
        const color = categoryColors[e.category] || 'var(--accent)';
        return `
            <a class="evidence-item" href="${escapeHtml(e.url)}" target="_blank" rel="noopener noreferrer">
                <div class="evidence-category-dot" style="background: ${color}"></div>
                <div class="evidence-body">
                    <div class="evidence-title">${escapeHtml(e.title)}</div>
                    <div class="evidence-snippet">${escapeHtml(e.snippet)}</div>
                    <div class="evidence-meta">
                        <span class="evidence-source">${escapeHtml(e.source)}</span>
                        <span>${e.category}</span>
                    </div>
                </div>
                <span class="evidence-external"><i class="fas fa-external-link-alt"></i></span>
            </a>
        `;
    }).join('');
}

function renderRisks(risks) {
    const list = $('riskList');

    if (!risks.length) {
        list.innerHTML = '<div class="no-risks"><i class="fas fa-shield-alt"></i> No significant risk factors identified</div>';
        return;
    }

    list.innerHTML = risks.map(r => `
        <div class="risk-item">
            <div class="risk-icon"><i class="fas fa-exclamation-triangle"></i></div>
            <div>
                <div class="risk-severity">${escapeHtml(r.severity)} Risk</div>
                <div class="risk-text">${escapeHtml(r.description)}</div>
            </div>
        </div>
    `).join('');
}

// ---------------------------------------------------------------
// Report Generation
// ---------------------------------------------------------------

function generateReport() {
    if (!currentCompanyData) return;

    const d = currentCompanyData;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });

    const W = 210; // A4 width mm
    const MARGIN = 18;
    const COL = W - MARGIN * 2;
    let y = 0;

    // ── Helpers ──────────────────────────────────────────────
    const hex = (h) => {
        const r = parseInt(h.slice(1, 3), 16);
        const g = parseInt(h.slice(3, 5), 16);
        const b = parseInt(h.slice(5, 7), 16);
        return [r, g, b];
    };
    const setFont = (size, style = 'normal', color = '#1a1a1a') => {
        doc.setFontSize(size);
        doc.setFont('helvetica', style);
        doc.setTextColor(...hex(color));
    };
    const rule = (yPos, color = '#e2e8f0') => {
        doc.setDrawColor(...hex(color));
        doc.setLineWidth(0.3);
        doc.line(MARGIN, yPos, W - MARGIN, yPos);
    };
    const wrap = (text, maxWidth) => doc.splitTextToSize(String(text || ''), maxWidth);

    // ── Header bar ───────────────────────────────────────────
    doc.setFillColor(...hex('#0f2419'));
    doc.rect(0, 0, W, 28, 'F');

    setFont(20, 'bold', '#4ade80');
    doc.text('SynthESG', MARGIN, 13);
    setFont(9, 'normal', '#86efac');
    doc.text('AI-Powered ESG Intelligence Report', MARGIN, 20);

    const dateStr = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    setFont(8, 'normal', '#86efac');
    doc.text(dateStr, W - MARGIN, 20, { align: 'right' });

    y = 38;

    // ── Company title ─────────────────────────────────────────
    setFont(18, 'bold', '#0f2419');
    doc.text(d.company_name, MARGIN, y);
    y += 7;

    setFont(9, 'normal', '#64748b');
    const meta = [d.sector, d.country].filter(Boolean).join('  ·  ');
    if (meta) { doc.text(meta, MARGIN, y); y += 5; }

    rule(y); y += 7;

    // ── Score summary box ─────────────────────────────────────
    doc.setFillColor(...hex('#f0fdf4'));
    doc.roundedRect(MARGIN, y, COL, 28, 3, 3, 'F');

    // Big score
    setFont(36, 'bold', '#16a34a');
    doc.text(String(d.esg_score), MARGIN + 14, y + 19, { align: 'center' });
    setFont(9, 'normal', '#64748b');
    doc.text('/100', MARGIN + 22, y + 19);

    // Rating
    setFont(15, 'bold', '#0f2419');
    doc.text(d.rating || '', MARGIN + 38, y + 13);
    setFont(8, 'normal', '#64748b');
    doc.text('Overall ESG Rating', MARGIN + 38, y + 19);

    // Pillars inline
    const pillars = [
        { label: 'Environmental', val: d.environmental, color: '#16a34a' },
        { label: 'Social', val: d.social, color: '#2563eb' },
        { label: 'Governance', val: d.governance, color: '#7c3aed' },
        { label: 'Innovation', val: d.innovation, color: '#d97706' },
    ];
    const pX = MARGIN + 90;
    const pGap = (COL - 90) / 4;
    pillars.forEach((p, i) => {
        const x = pX + i * pGap + pGap / 2;
        setFont(13, 'bold', p.color);
        doc.text(String(p.val), x, y + 13, { align: 'center' });
        setFont(7, 'normal', '#64748b');
        doc.text('/25', x + 5, y + 13);
        setFont(7, 'normal', '#374151');
        doc.text(p.label, x, y + 20, { align: 'center' });
    });

    y += 36;

    // ── Section helper ─────────────────────────────────────────
    const section = (title, icon = '') => {
        if (y > 260) { doc.addPage(); y = 20; }
        setFont(11, 'bold', '#0f2419');
        doc.text(`${icon}  ${title}`, MARGIN, y);
        y += 3;
        rule(y, '#bbf7d0'); y += 5;
    };

    // ── Research Insights ──────────────────────────────────────
    const insights = d.research_insights || [];
    if (insights.length) {
        section('Research Insights');
        insights.forEach((ins) => {
            if (y > 265) { doc.addPage(); y = 20; }
            // Category chip
            doc.setFillColor(...hex('#dcfce7'));
            doc.roundedRect(MARGIN, y - 3, 40, 5, 1, 1, 'F');
            setFont(7, 'bold', '#15803d');
            doc.text(ins.category || '', MARGIN + 2, y + 1);

            y += 5;
            setFont(8, 'normal', '#374151');
            const lines = wrap(ins.finding, COL);
            doc.text(lines, MARGIN, y);
            y += lines.length * 4 + 4;
        });
        y += 2;
    }

    // ── Source Evidence ────────────────────────────────────────
    const evidence = (d.news_evidence || []).slice(0, 6);
    if (evidence.length) {
        section('Source Evidence');
        evidence.forEach((ev, i) => {
            if (y > 265) { doc.addPage(); y = 20; }
            setFont(8, 'bold', '#0f2419');
            const titleLines = wrap(`${i + 1}. ${ev.title}`, COL);
            doc.text(titleLines, MARGIN, y);
            y += titleLines.length * 4;

            if (ev.snippet) {
                setFont(7, 'normal', '#64748b');
                const snipLines = wrap(ev.snippet, COL);
                doc.text(snipLines, MARGIN + 3, y);
                y += snipLines.length * 3.5;
            }

            setFont(7, 'normal', '#2563eb');
            doc.text(ev.url || '', MARGIN + 3, y, { maxWidth: COL });
            y += 5;
        });
        y += 2;
    }

    // ── Methodology ────────────────────────────────────────────
    if (d.methodology) {
        if (y > 255) { doc.addPage(); y = 20; }
        section('Methodology');
        setFont(8, 'normal', '#374151');
        const mLines = wrap(
            `${d.methodology.framework}. Max pillar score: ${d.methodology.max_pillar_score}/25. ` +
            (d.methodology.research_applied ? 'Scores adjusted using real-time research data.' : ''),
            COL
        );
        doc.text(mLines, MARGIN, y);
        y += mLines.length * 4 + 4;
    }

    // ── Footer on every page ───────────────────────────────────
    const totalPages = doc.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
        doc.setPage(p);
        doc.setFillColor(...hex('#0f2419'));
        doc.rect(0, 287, W, 10, 'F');
        setFont(7, 'normal', '#86efac');
        doc.text('Generated by SynthESG · synthESG.ai', MARGIN, 293);
        doc.text(`Page ${p} of ${totalPages}`, W - MARGIN, 293, { align: 'right' });
    }

    // ── Save ───────────────────────────────────────────────────
    const filename = `SynthESG_${d.company_name.replace(/\s+/g, '_')}_ESG_Report.pdf`;
    doc.save(filename);
}

// ---------------------------------------------------------------
// Error Display
// ---------------------------------------------------------------

function showError(title, message, suggestion, severity) {
    const iconMap = { danger: 'fas fa-times-circle', warning: 'fas fa-exclamation-circle' };

    $('results').innerHTML = `
        <div class="error-container">
            <div class="error-icon-wrapper ${severity}">
                <i class="${iconMap[severity] || iconMap.danger}"></i>
            </div>
            <h2>${escapeHtml(title)}</h2>
            <p>${escapeHtml(message || 'Something went wrong.')}</p>
            ${suggestion ? `<p style="color: var(--text-muted); font-size: 13px; margin-bottom: 24px;">${escapeHtml(suggestion)}</p>` : ''}
            <button class="action-btn secondary" onclick="newSearch()">
                <i class="fas fa-arrow-left"></i> Try Again
            </button>
        </div>
    `;
    showSection('results');
}

// ---------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------

function newSearch() {
    currentCompanyData = null;
    $('companyName').value = '';
    showSection('hero');

    // Reset ring
    $('ringFill').style.strokeDashoffset = 326.73;

    // Reset bars
    ['envBar', 'socialBar', 'govBar', 'innovBar'].forEach(id => {
        $(id).style.width = '0%';
    });

    // Restore results HTML if replaced by error
    if (!document.querySelector('.company-card')) {
        window.location.reload();
        return;
    }

    $('companyName').focus();
}

function showSection(section) {
    const hero = document.querySelector('.hero');
    const loading = $('loading');
    const results = $('results');

    hero.style.display = section === 'hero' ? 'flex' : 'none';
    loading.style.display = section === 'loading' ? 'flex' : 'none';
    results.style.display = section === 'results' ? 'block' : 'none';

    if (section !== 'hero') window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateLoadingSteps(active) {
    for (let i = 1; i <= 3; i++) {
        const step = $(`step${i}`);
        step.className = 'step';
        if (i < active) {
            step.className = 'step done';
            step.querySelector('i').className = 'fas fa-check-circle';
        } else if (i === active) {
            step.className = 'step active';
            step.querySelector('i').className = 'fas fa-circle-notch fa-spin';
        } else {
            step.querySelector('i').className = 'far fa-circle';
        }
    }
}

// ---------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------

function generateFallbackLogo(name) {
    const initial = (name || '?').charAt(0).toUpperCase();
    const svg = `<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">` +
        `<rect width="64" height="64" fill="#1a251f" rx="8"/>` +
        `<text x="32" y="32" font-family="Inter,Arial" font-size="22" font-weight="600" ` +
        `fill="#4ade80" text-anchor="middle" dy=".35em">${initial}</text></svg>`;
    return 'data:image/svg+xml;base64,' + btoa(svg);
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------
// API Health Check
// ---------------------------------------------------------------

async function checkApiHealth() {
    const dot = $('statusDot');
    const text = $('statusText');

    dot.className = 'status-dot checking';
    text.textContent = 'Checking…';

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${CONFIG.API_ENDPOINT}/api/v1/health`, {
            signal: controller.signal,
        });
        clearTimeout(timeout);

        if (response.ok) {
            dot.className = 'status-dot online';
            text.textContent = 'API Online';
        } else {
            dot.className = 'status-dot offline';
            text.textContent = 'API Error';
        }
    } catch {
        dot.className = 'status-dot offline';
        text.textContent = 'Offline';
    }
}

// ---------------------------------------------------------------
// Init
// ---------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    $('companyName').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            analyzeCompany();
        }
    });

    // Check API status on load and every 60s
    checkApiHealth();
    setInterval(checkApiHealth, 60000);
});