// Configuration - Real AWS API Gateway URL
const CONFIG = {
    API_ENDPOINT: 'https://2n6a4d3y55.execute-api.ap-southeast-5.amazonaws.com/prod',
    REGION: 'ap-southeast-5'
};

// Global variables for news pagination
let currentNewsPage = 0;
let newsPerPage = 3;
let allNewsItems = [];
let currentCompanyData = null;

async function analyzeCompany() {
    const companyInput = document.getElementById('companyName').value.trim();
    if (!companyInput) {
        alert('Please enter a company name');
        return;
    }

    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    try {
        // Call professional AWS API
        const response = await fetch(`${CONFIG.API_ENDPOINT}/api/v1/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                company_name: companyInput
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        // Check for company validation errors
        if (data.error === 'company_not_found') {
            showCompanyNotFoundError(data);
            return;
        }
        
        // Check for insufficient ESG data error
        if (data.error === 'insufficient_esg_data') {
            showInsufficientESGDataError(data);
            return;
        }
        
        currentCompanyData = data;
        allNewsItems = data.news_evidence || [];
        displayResults(data);

    } catch (error) {
        console.error('API call failed:', error);
        document.getElementById('loading').style.display = 'none';
        alert(`Failed to analyze ${companyInput}. Error: ${error.message}`);
    }
}

function showInsufficientDataError(errorData) {
    document.getElementById('loading').style.display = 'none';
    
    const errorHtml = `
        <div style="background: rgba(255, 255, 255, 0.95); padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <div style="color: #e74c3c; font-size: 3rem; margin-bottom: 20px;">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h2 style="color: #e74c3c; margin-bottom: 15px;">Insufficient ESG Data</h2>
            <p style="font-size: 18px; margin-bottom: 20px; color: #666;">
                ${errorData.message}
            </p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>Data Quality Assessment:</h4>
                <p>Quality Score: ${errorData.data_quality.quality_score}/${errorData.data_quality.max_score}</p>
                <p>Data Sources Found: ${errorData.data_quality.data_sources}</p>
                <p>Status: ${errorData.data_quality.recommendation}</p>
            </div>
            <p style="color: #666; margin-bottom: 30px;">
                ${errorData.suggestion}
            </p>
            <button class="btn btn-primary" onclick="newSearch()">
                <i class="fas fa-search"></i>
                Try Another Company
            </button>
        </div>
    `;
    
    document.getElementById('results').innerHTML = errorHtml;
    document.getElementById('results').style.display = 'block';
}

function showCompanyNotFoundError(errorData) {
    document.getElementById('loading').style.display = 'none';
    
    const errorHtml = `
        <div style="background: rgba(255, 255, 255, 0.95); padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <div style="color: #e74c3c; font-size: 3rem; margin-bottom: 20px;">
                <i class="fas fa-building"></i>
            </div>
            <h2 style="color: #e74c3c; margin-bottom: 15px;">Company Not Found</h2>
            <p style="font-size: 18px; margin-bottom: 20px; color: #666;">
                ${errorData.message}
            </p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>Validation Results:</h4>
                <p>Confidence Level: ${errorData.validation_confidence}%</p>
                <p>Status: Company could not be verified as legitimate business</p>
            </div>
            <p style="color: #666; margin-bottom: 30px;">
                ${errorData.suggestion}
            </p>
            <button class="btn btn-primary" onclick="newSearch()">
                <i class="fas fa-search"></i>
                Try Another Company
            </button>
        </div>
    `;
    
    document.getElementById('results').innerHTML = errorHtml;
    document.getElementById('results').style.display = 'block';
}

function showInsufficientESGDataError(errorData) {
    document.getElementById('loading').style.display = 'none';
    
    const errorHtml = `
        <div style="background: rgba(255, 255, 255, 0.95); padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <div style="color: #f39c12; font-size: 3rem; margin-bottom: 20px;">
                <i class="fas fa-chart-line"></i>
            </div>
            <h2 style="color: #f39c12; margin-bottom: 15px;">Insufficient ESG Data</h2>
            <p style="font-size: 18px; margin-bottom: 20px; color: #666;">
                ${errorData.message}
            </p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>Data Analysis:</h4>
                <p>ESG News Found: ${errorData.news_found} articles</p>
                <p>Minimum Required: 2 articles</p>
                <p>Status: Insufficient public ESG reporting</p>
            </div>
            <p style="color: #666; margin-bottom: 30px;">
                ${errorData.suggestion}
            </p>
            <button class="btn btn-primary" onclick="newSearch()">
                <i class="fas fa-search"></i>
                Try Another Company
            </button>
        </div>
    `;
    
    document.getElementById('results').innerHTML = errorHtml;
    document.getElementById('results').style.display = 'block';
}

function displayResults(data) {
    // Ensure elements exist before accessing them
    const resultCompany = document.getElementById('resultCompany');
    if (!resultCompany) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Populate company information
    resultCompany.textContent = data.company_name;
    document.getElementById('sectorBadge').textContent = data.sector || data.raw_data?.company_profile?.sector || 'Unknown';
    document.getElementById('countryBadge').textContent = data.country || 'Global';
    
    // Set company logo (fallback to generated)
    const logoImg = document.getElementById('companyLogo');
    logoImg.src = data.company_logo || generateLogo(data.company_name);
    logoImg.onerror = function() {
        this.src = generateLogo(data.company_name);
    };

    // Display scientific ESG scores
    if (data.final_scores) {
        document.getElementById('esgScore').textContent = data.final_scores.overall;
        document.getElementById('esgRating').textContent = data.final_scores.rating;
        document.getElementById('envScore').textContent = data.final_scores.environmental;
        document.getElementById('socialScore').textContent = data.final_scores.social;
        document.getElementById('govScore').textContent = data.final_scores.governance;
        document.getElementById('innovScore').textContent = data.final_scores.innovation;
    } else {
        // Fallback for old format
        document.getElementById('esgScore').textContent = data.esg_score || 0;
        document.getElementById('esgRating').textContent = data.rating || 'Unknown';
        document.getElementById('envScore').textContent = data.environmental || 0;
        document.getElementById('socialScore').textContent = data.social || 0;
        document.getElementById('govScore').textContent = data.governance || 0;
        document.getElementById('innovScore').textContent = data.innovation || 0;
    }

    // Display scientific methodology info
    if (data.methodology) {
        const methodologyInfo = document.createElement('div');
        methodologyInfo.style.cssText = 'background: #e8f5e8; border: 1px solid #87A96B; padding: 15px; border-radius: 10px; margin: 20px 0;';
        methodologyInfo.innerHTML = `
            <h4>🔬 Scientific ESG Analysis</h4>
            <p><strong>Framework:</strong> ${data.methodology.framework}</p>
            <p><strong>Method:</strong> ${data.methodology.calculation_method}</p>
            <p><strong>Confidence:</strong> ${data.methodology.confidence_interval.lower_bound} - ${data.methodology.confidence_interval.upper_bound} (${data.methodology.confidence_interval.confidence_level})</p>
            <p><strong>Industry Benchmarking:</strong> ${data.methodology.industry_benchmarking ? 'Yes' : 'No'}</p>
        `;
        document.getElementById('results').insertBefore(methodologyInfo, document.getElementById('results').firstChild);
    }

    // Display raw data transformation
    if (data.raw_data) {
        displayRawDataTransformation(data);
    }

    // Display news evidence (fallback to empty if not available)
    allNewsItems = data.news_evidence || [];
    displayNewsEvidence();

    // Show results
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
}

function displayRawDataTransformation(data) {
    // Create raw data section
    const rawDataSection = document.createElement('div');
    rawDataSection.style.cssText = 'margin: 30px 0; padding: 25px; background: #f8f9fa; border-radius: 15px; border-left: 4px solid #87A96B;';
    
    rawDataSection.innerHTML = `
        <h3>📊 Raw Data → ESG Transformation</h3>
        <p>Scientific calculation showing how raw metrics are transformed into ESG scores</p>
        
        <div class="transformation-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
            ${generateTransformationCard('Environmental', data.raw_data.environmental_metrics, data.esg_analysis.environmental)}
            ${generateTransformationCard('Social', data.raw_data.social_metrics, data.esg_analysis.social)}
            ${generateTransformationCard('Governance', data.raw_data.governance_metrics, data.esg_analysis.governance)}
            ${generateTransformationCard('Innovation', data.raw_data.innovation_metrics, data.esg_analysis.innovation)}
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 10px;">
            <h4>🏢 Company Profile</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div><strong>Employees:</strong> ${data.raw_data.company_profile.employees.toLocaleString()}</div>
                <div><strong>Revenue:</strong> $${data.raw_data.company_profile.revenue_usd_millions.toLocaleString()}M</div>
                <div><strong>Market Cap:</strong> $${data.raw_data.company_profile.market_cap_usd_billions}B</div>
                <div><strong>Sector:</strong> ${data.raw_data.company_profile.sector}</div>
            </div>
        </div>
    `;
    
    // Insert after company header
    const companyHeader = document.querySelector('.company-header');
    companyHeader.parentNode.insertBefore(rawDataSection, companyHeader.nextSibling);
}

function generateTransformationCard(category, rawData, analysis) {
    const categoryKey = category.toLowerCase();
    const keyMetrics = analysis.key_metrics;
    const score = analysis.score;
    
    let metricsHtml = '';
    for (const [key, value] of Object.entries(keyMetrics)) {
        const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const displayValue = typeof value === 'number' ? 
            (value % 1 === 0 ? value.toLocaleString() : value.toFixed(2)) : value;
        metricsHtml += `<div><strong>${displayKey}:</strong> ${displayValue}</div>`;
    }
    
    return `
        <div style="background: white; padding: 20px; border-radius: 10px; border: 2px solid #e9ecef;">
            <h4 style="color: #87A96B; margin-bottom: 15px;">📈 ${category}</h4>
            
            <div style="margin-bottom: 15px;">
                <h5>Raw Metrics:</h5>
                ${metricsHtml}
            </div>
            
            <div style="margin-bottom: 15px;">
                <h5>Calculation Process:</h5>
                <div style="font-size: 12px; color: #666;">
                    • Industry benchmarking applied<br/>
                    • Z-score normalization used<br/>
                    • Weighted scoring methodology<br/>
                    • Statistical confidence: 95%
                </div>
            </div>
            
            <div style="background: #87A96B; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                <strong>Final Score: ${score}/100</strong>
            </div>
        </div>
    `;
}

    // Display real news evidence with pagination
    displayNewsEvidence();

    // Show results
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
}

function displayNewsEvidence() {
    const evidenceGrid = document.getElementById('evidenceGrid');
    const evidenceSection = document.querySelector('.evidence-section');
    
    // Clear existing content
    evidenceGrid.innerHTML = '';
    
    // Remove existing pagination if any
    const existingPagination = evidenceSection.querySelector('.news-pagination');
    if (existingPagination) {
        existingPagination.remove();
    }
    
    if (allNewsItems.length === 0) {
        evidenceGrid.innerHTML = '<p>No recent ESG news found for this company.</p>';
        return;
    }
    
    // Calculate pagination
    const startIndex = currentNewsPage * newsPerPage;
    const endIndex = Math.min(startIndex + newsPerPage, allNewsItems.length);
    const currentNews = allNewsItems.slice(startIndex, endIndex);
    
    // Display current page news
    currentNews.forEach((news, index) => {
        const evidenceItem = document.createElement('div');
        evidenceItem.className = 'evidence-item clickable-news';
        
        // Add "Used in ESG Scoring" indicator
        const usedInScoring = news.used_in_scoring ? 
            '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; margin-left: 10px;">Used in ESG Scoring</span>' : '';
        
        evidenceItem.innerHTML = `
            <div class="news-header">
                <h5>${news.title}</h5>
                <span class="news-source">${news.source}</span>
            </div>
            <div class="news-content">
                <p>${news.snippet}</p>
                <div class="news-meta">
                    <span class="news-date">${news.date}</span>
                    <span class="relevance-score">Relevance: ${news.relevance_score}/10</span>
                </div>
                ${usedInScoring}
            </div>
            <div class="news-actions">
                <button onclick="openNewsLink('${news.url}')" class="news-link-btn">
                    <i class="fas fa-external-link-alt"></i>
                    Read Full Article
                </button>
            </div>
        `;
        evidenceGrid.appendChild(evidenceItem);
    });
    
    // Add pagination controls at the bottom of evidence section (not in grid)
    if (allNewsItems.length > newsPerPage) {
        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'news-pagination';
        
        const totalPages = Math.ceil(allNewsItems.length / newsPerPage);
        const currentPageNum = currentNewsPage + 1;
        
        paginationDiv.innerHTML = `
            <div class="pagination-info">
                Showing ${startIndex + 1}-${endIndex} of ${allNewsItems.length} ESG news articles used in analysis
            </div>
            <div class="pagination-controls">
                <button onclick="previousNewsPage()" ${currentNewsPage === 0 ? 'disabled' : ''} class="pagination-btn">
                    <i class="fas fa-chevron-left"></i>
                    Previous
                </button>
                <span class="page-indicator">Page ${currentPageNum} of ${totalPages}</span>
                <button onclick="nextNewsPage()" ${currentNewsPage >= totalPages - 1 ? 'disabled' : ''} class="pagination-btn">
                    Next
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        // Append pagination to evidence section (not grid)
        evidenceSection.appendChild(paginationDiv);
    }
}

function previousNewsPage() {
    if (currentNewsPage > 0) {
        currentNewsPage--;
        displayNewsEvidence();
    }
}

function nextNewsPage() {
    const totalPages = Math.ceil(allNewsItems.length / newsPerPage);
    if (currentNewsPage < totalPages - 1) {
        currentNewsPage++;
        displayNewsEvidence();
    }
}

function openNewsLink(url) {
    window.open(url, '_blank', 'noopener,noreferrer');
}

async function generateReport() {
    if (!currentCompanyData) {
        alert('No company data available for report generation');
        return;
    }
    
    try {
        // Show loading state
        const reportBtn = document.getElementById('generateReportBtn');
        const originalText = reportBtn.innerHTML;
        reportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';
        reportBtn.disabled = true;
        
        const response = await fetch(`${CONFIG.API_ENDPOINT}/api/v1/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: currentCompanyData.company_name,
                company_data: currentCompanyData
            })
        });

        if (response.ok) {
            const result = await response.json();
            
            // Create download link
            const downloadLink = document.createElement('a');
            downloadLink.href = result.download_url;
            downloadLink.download = `${currentCompanyData.company_name}_ESG_Report.pdf`;
            downloadLink.click();
            
            alert('✅ Professional ESG report generated successfully! Download started.');
        } else {
            throw new Error('Report generation failed');
        }
    } catch (error) {
        console.error('Report generation error:', error);
        alert('❌ Report generation failed. Please try again.');
    } finally {
        // Reset button
        const reportBtn = document.getElementById('generateReportBtn');
        reportBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Generate Full Report';
        reportBtn.disabled = false;
    }
}

function generateLogo(company) {
    const initial = company.charAt(0).toUpperCase();
    const svg = `<svg width="80" height="80" xmlns="http://www.w3.org/2000/svg"><rect width="80" height="80" fill="#87A96B" rx="12"/><text x="40" y="40" font-family="Inter, Arial" font-size="24" fill="white" text-anchor="middle" dy=".3em">${initial}</text></svg>`;
    return 'data:image/svg+xml;base64,' + btoa(svg);
}

function newSearch() {
    // Simple fix: reload page to reset interface after error
    window.location.reload();
}

// Event listeners
document.getElementById('companyName').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        analyzeCompany();
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('ESGenius AI - Enhanced Professional System Loaded');
});
