// Register DataLabels Plugin globally
Chart.register(ChartDataLabels);

// Navigation
function showSection(sectionId) {
    document.querySelectorAll('section').forEach(s => {
        s.classList.remove('section-active');
        s.classList.add('section-hidden');
    });
    document.getElementById('section-' + sectionId).classList.remove('section-hidden');
    document.getElementById('section-' + sectionId).classList.add('section-active');

    document.querySelectorAll('.sidebar-nav li').forEach(li => li.classList.remove('active'));
    event.currentTarget.parentElement.classList.add('active');
}

function showAdminSection(sectionId) { showSection(sectionId); }

// Modals
function promptScan() { document.getElementById('permissionModal').classList.remove('d-none'); }
function closeModal(id) { document.getElementById(id).classList.add('d-none'); }

function openProfileModal() { document.getElementById('profileModal').classList.remove('d-none'); }

function submitProfile(event) {
    event.preventDefault();
    const btn = document.getElementById('btnSaveProfile');
    btn.disabled = true; btn.innerText = 'Saving...';
    
    const form = document.getElementById('profileForm');
    const formData = new FormData(form);
    
    fetch('/update_profile', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            location.reload();
        } else {
            document.getElementById('profileError').innerText = data.error;
            document.getElementById('profileError').classList.remove('d-none');
            btn.disabled = false; btn.innerText = 'Save Changes';
        }
    }).catch(err => {
        document.getElementById('profileError').innerText = "Network error occurred.";
        document.getElementById('profileError').classList.remove('d-none');
        btn.disabled = false; btn.innerText = 'Save Changes';
    });
}

function openEmailModal(reportId) {
    document.getElementById('emailReportId').value = reportId;
    document.getElementById('emailModal').classList.remove('d-none');
    document.getElementById('emailMsg').innerText = '';
    document.getElementById('emailMsg').className = 'mt-10';
}

function sendEmailReport() {
    const reportId = document.getElementById('emailReportId').value;
    const email = document.getElementById('recipientEmail').value;
    const btn = document.getElementById('btnSendEmail');
    const msg = document.getElementById('emailMsg');
    
    if(!email) { msg.innerText = "Please enter an email."; msg.className = "mt-10 text-danger"; return; }
    
    btn.disabled = true; btn.innerText = "Sending...";
    msg.innerText = "Sending email, please wait..."; msg.className = "mt-10 text-muted";
    
    fetch('/send_email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId, email: email })
    }).then(res => res.json()).then(data => {
        if(data.success) {
            msg.innerText = "Email sent successfully!"; msg.className = "mt-10 text-success";
            setTimeout(() => closeModal('emailModal'), 2000);
        } else {
            msg.innerText = data.error; msg.className = "mt-10 text-danger";
        }
        btn.disabled = false; btn.innerText = "Send Email";
    }).catch(err => {
        msg.innerText = "Error sending email."; msg.className = "mt-10 text-danger";
        btn.disabled = false; btn.innerText = "Send Email";
    });
}

function downloadReportPDF(reportId) {
    const report = allReports.find(r => r.id === reportId);
    if(!report) return;
    
    const container = document.getElementById('pdfContainer');
    container.innerHTML = `
        <div style="padding: 40px; font-family: sans-serif; color: #1F2937;">
            <h1 style="color: #7C3AED; border-bottom: 2px solid #E5E7EB; padding-bottom: 10px;">SysDiag Pro Report</h1>
            <p><strong>Date:</strong> ${report.scan_date} ${report.scan_time}</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr><th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Metric</th><th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Value</th></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">Security Score</td><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>${report.security_score}/100</b></td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">CPU Usage</td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${report.cpu_usage}%</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">RAM Usage</td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${report.ram_usage}%</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">Disk Usage</td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${report.disk_usage}%</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">Network</td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${report.network_status}</td></tr>
            </table>
            <p style="margin-top:40px; font-size:12px; color: #6B7280; text-align: center;">Generated by SysDiag Pro</p>
        </div>
    `;
    container.classList.remove('d-none');
    
    var opt = {
      margin:       1,
      filename:     'SysDiag_Report_' + report.scan_date + '.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2 },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(container).save().then(() => {
        container.classList.add('d-none');
        container.innerHTML = '';
    });
}

// Search Filter
function filterTable(tableId, inputId) {
    var input, filter, table, tr, td, i, txtValue;
    input = document.getElementById(inputId);
    filter = input.value.toUpperCase();
    table = document.getElementById(tableId);
    tr = table.getElementsByTagName("tr");
    for (i = 1; i < tr.length; i++) {
        tr[i].style.display = "none";
        td = tr[i].getElementsByTagName("td");
        for (var j = 0; j < td.length; j++) {
            if (td[j]) {
                if (td[j].innerHTML.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                    break;
                }
            }
        }
    }
}

// Animation Utilities
function animateCounter(element, target, suffix='') {
    let current = parseInt(element.innerText) || 0;
    target = Math.round(target);
    if(current === target) return;
    let step = target > current ? 1 : -1;
    let speed = Math.max(10, Math.abs(200 / (target - current)));
    
    let timer = setInterval(() => {
        current += step;
        element.innerText = current + suffix;
        if (current === target) clearInterval(timer);
    }, speed);
}

// Scan Process
function startScan() {
    closeModal('permissionModal');
    const overlay = document.getElementById('scanningOverlay');
    overlay.classList.remove('d-none');
    
    let progress = 0;
    const bar = document.getElementById('scan-progress');
    const pct = document.getElementById('scan-percentage');
    const statusText = document.getElementById('scan-status-text');
    
    const statuses = [
        "Initializing scan engine...",
        "Scanning CPU architecture...",
        "Checking RAM allocation...",
        "Scanning Disk storage...",
        "Pinging Network interfaces...",
        "Testing Security Ports...",
        "Checking Firewall & AV...",
        "Generating comprehensive report..."
    ];

    fetch('/scan', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if(data.error) { alert("Error: " + data.error); location.reload(); return; }
            const interval = setInterval(() => {
                progress += 2;
                bar.style.width = progress + '%';
                animateCounter(pct, progress, '%');

                let idx = Math.floor(progress / 12.5);
                if(idx < statuses.length) statusText.innerText = statuses[idx];

                if (progress >= 100) {
                    clearInterval(interval);
                    setTimeout(() => location.reload(), 500);
                }
            }, 80);
        })
        .catch(err => { alert("Scan failed!"); overlay.classList.add('d-none'); });
}

// Speed Test Process (V3 Dashboard Style)
function runSpeedTest() {
    const loader = document.getElementById('speedTestLoader');
    const grid = document.getElementById('speedTestGrid');
    const emptyState = document.getElementById('speedTestEmptyState');
    const btnText = document.getElementById('btnRunSpeedText');
    const btn = document.getElementById('btnRunSpeed');
    
    loader.classList.remove('d-none');
    grid.classList.add('d-none');
    if(emptyState) emptyState.classList.add('d-none');
    btn.disabled = true; btnText.innerText = "Running...";
    
    fetch('/speedtest', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            loader.classList.add('d-none');
            btn.disabled = false; btnText.innerText = "Run Again";
            if(data.success) {
                grid.classList.remove('d-none');
                
                let statusColor = "#16A34A"; let statusText = "Excellent";
                if (data.ping > 100 || data.download < 10) { statusColor = "#EF4444"; statusText = "Poor"; }
                else if (data.ping > 50 || data.download < 50) { statusColor = "#F59E0B"; statusText = "Average"; }
                else if (data.ping > 20 || data.download < 100) { statusColor = "#7C3AED"; statusText = "Good"; }

                grid.innerHTML = `
                    <div class="speed-card card-anim" style="border-bottom-color: #7C3AED;">
                        <h3>Download</h3>
                        <div class="speed-val">${data.download} <span class="speed-unit">Mbps</span></div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.1s; border-bottom-color: #EC4899;">
                        <h3>Upload</h3>
                        <div class="speed-val">${data.upload} <span class="speed-unit">Mbps</span></div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.2s; border-bottom-color: #A78BFA;">
                        <h3>Ping</h3>
                        <div class="speed-val">${data.ping} <span class="speed-unit">ms</span></div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.3s; border-bottom-color: #F59E0B;">
                        <h3>Jitter</h3>
                        <div class="speed-val">${data.jitter} <span class="speed-unit">ms</span></div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.4s; border-bottom-color: ${statusColor};">
                        <h3>Status</h3>
                        <div class="speed-val" style="font-size: 20px; color: ${statusColor};"><span class="speed-status-indicator" style="background:${statusColor};"></span>${statusText}</div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.5s; border-bottom-color: #9CA3AF;">
                        <h3>ISP</h3>
                        <div class="speed-val" style="font-size: 16px;">${data.isp}</div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.6s; border-bottom-color: #9CA3AF;">
                        <h3>Public IP</h3>
                        <div class="speed-val" style="font-size: 16px;">${data.ip}</div>
                    </div>
                    <div class="speed-card card-anim" style="animation-delay: 0.7s; border-bottom-color: #9CA3AF;">
                        <h3>Location</h3>
                        <div class="speed-val" style="font-size: 16px;">${data.server}</div>
                    </div>
                `;
            } else {
                alert("Speed test failed: " + data.error);
                if(emptyState) emptyState.classList.remove('d-none');
            }
        }).catch(err => {
            loader.classList.add('d-none');
            btn.disabled = false; btnText.innerText = "Run Speed Test";
            alert("Error running speed test.");
            if(emptyState) emptyState.classList.remove('d-none');
        });
}

// Initialization for Dashboard
document.addEventListener("DOMContentLoaded", () => {
    if (typeof lastScanRaw !== 'undefined' && lastScanRaw) {
        // Populate Issues List
        const issuesContainer = document.getElementById('issues-list');
        const issues = JSON.parse(lastScanRaw.issues_found);
        const fixes = JSON.parse(lastScanRaw.fixes_suggested);
        
        // Quick Fix Recommendations
        const qfContainer = document.getElementById('quick-fixes-list');
        if(issues.length === 0) {
            qfContainer.innerHTML = `
                <div class="healthy-msg">
                    <i class="fas fa-check-circle"></i>
                    <h4>Your system is healthy! No fixes needed.</h4>
                </div>
            `;
        } else {
            let qfHtml = '';
            issues.forEach((issue, idx) => {
                let priorityClass = 'bg-low'; let priorityText = 'Low'; let icon = 'fa-info-circle';
                if(issue.includes("Critical") || issue.includes("Disconnected")) { priorityClass = 'bg-high'; priorityText = 'High'; icon = 'fa-times-circle'; }
                else if(issue.includes("Warning") || issue.includes("High")) { priorityClass = 'bg-medium'; priorityText = 'Medium'; icon = 'fa-exclamation-triangle'; }

                qfHtml += `
                <div class="qf-card">
                    <div class="qf-badge ${priorityClass}">${priorityText}</div>
                    <div class="qf-header">
                        <i class="fas ${icon} qf-icon text-danger"></i>
                        <span class="qf-title">${issue}</span>
                    </div>
                    <div class="qf-desc">Performance issue detected during recent diagnostic scan.</div>
                    <div class="qf-fix"><i class="fas fa-tools"></i> Fix: ${fixes[idx]}</div>
                </div>`;
            });
            if(qfContainer) qfContainer.innerHTML = qfHtml;
        }

        renderUserCharts(lastScanRaw, allReports);
    }
});

function renderUserCharts(current, history) {
    Chart.defaults.color = '#1F2937';

    // Grouped Bar Chart for History (Last 10 Scans)
    if(history && history.length > 0) {
        const histRev = [...history].slice(0, 10).reverse();
        const ctxBar = document.getElementById('historyBarChart');
        if(ctxBar) {
            new Chart(ctxBar.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: histRev.map(h => h.scan_date),
                    datasets: [
                        { label: 'CPU', data: histRev.map(h => h.cpu_usage), backgroundColor: '#7C3AED', borderRadius: 4 },
                        { label: 'RAM', data: histRev.map(h => h.ram_usage), backgroundColor: '#EC4899', borderRadius: 4 },
                        { label: 'Disk', data: histRev.map(h => h.disk_usage), backgroundColor: '#A78BFA', borderRadius: 4 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { y: { max: 100, min: 0, grid: { color: '#E5E7EB' } }, x: { grid: { display: false } } },
                    plugins: {
                        legend: { display: true, position: 'top' },
                        datalabels: { color: '#1F2937', anchor: 'end', align: 'top', formatter: Math.round, font: { size: 10 } }
                    }
                }
            });
        }
    }

    // Security Score Horizontal Bar Chart
    const secDetails = JSON.parse(current.security_details);
    const secCtx = document.getElementById('secBarChart');
    if(secCtx) {
        document.getElementById('secGaugeText').innerText = `${current.security_score}/100`;
        let secStatus = "Critical"; let statColor = "#EF4444"; let sug = "Your system is at severe risk. Apply fixes immediately.";
        if(current.security_score > 40) { secStatus = "Needs Attention"; statColor = "#F59E0B"; sug = "Review the missing security checkpoints below and enable them.";}
        if(current.security_score > 70) { secStatus = "Good"; statColor = "#7C3AED"; sug = "Your system is reasonably secure. Review minor warnings.";}
        if(current.security_score > 90) { secStatus = "Excellent"; statColor = "#16A34A"; sug = "Great job! Your system configuration is highly secure.";}
        
        document.getElementById('secStatusText').innerText = `Status: ${secStatus}`;
        document.getElementById('secStatusText').style.color = statColor;
        document.getElementById('secSuggestionsText').innerText = sug;

        new Chart(secCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: secDetails.map(d => d.name),
                datasets: [{
                    label: 'Security Check Points',
                    data: secDetails.map(d => parseInt(d.points.replace('+',''))),
                    backgroundColor: secDetails.map(d => parseInt(d.points.replace('+','')) > 0 ? '#7C3AED' : '#EC4899'),
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                scales: { x: { max: 20, grid: { color: '#E5E7EB' } }, y: { grid: { display: false } } },
                plugins: {
                    legend: { display: false },
                    datalabels: { color: '#1F2937', anchor: 'end', align: 'right', formatter: function(val) { return val + " pts"; }, font: { weight: 'bold' } }
                }
            }
        });
    }
}

function deleteReport(id) {
    if(confirm("Are you sure you want to delete this report?")) {
        fetch(`/report/${id}`, { method: 'DELETE' }).then(res => res.json()).then(data => { if(data.success) location.reload(); });
    }
}
