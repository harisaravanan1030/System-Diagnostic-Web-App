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

function showAdminSection(sectionId) {
    showSection(sectionId);
}

// Modals
function promptScan() { document.getElementById('permissionModal').classList.remove('d-none'); }
function closeModal(id) { document.getElementById('id').classList.add('d-none'); }
if(document.getElementById('permissionModal')){
    window.closeModal = function(id) { document.getElementById(id).classList.add('d-none'); }
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

function updateColor(elementId, value) {
    const el = document.getElementById(elementId);
    if(!el) return;
    el.classList.remove('text-success', 'text-warning', 'text-danger');
    if (value < 60) el.classList.add('text-success');
    else if (value < 80) el.classList.add('text-warning');
    else el.classList.add('text-danger');
}

// Color constants matching prompt (only for donut charts if not changed, else follow instructions)
const COLORS = {
    cpu: '#7C3AED',
    ram: '#7c3aed',
    disk: '#ff6b35',
    empty: '#2a2a3a'
};

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

// Speed Test Process
function runSpeedTest() {
    const loader = document.getElementById('speedTestLoader');
    const gauges = document.getElementById('speedGauges');
    
    loader.classList.remove('d-none');
    gauges.classList.add('d-none');
    
    fetch('/speedtest', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            loader.classList.add('d-none');
            if(data.success) {
                gauges.classList.remove('d-none');
                
                let dl = document.getElementById('downloadVal');
                let ul = document.getElementById('uploadVal');
                let pl = document.getElementById('pingVal');
                
                dl.innerText = '0 Mbps'; ul.innerText = '0 Mbps'; pl.innerText = '0 ms';
                animateCounter(dl, data.download, ' Mbps');
                animateCounter(ul, data.upload, ' Mbps');
                animateCounter(pl, data.ping, ' ms');
                
                // Update ping color
                pl.classList.remove('text-success', 'text-warning', 'text-danger');
                if(data.ping < 20) pl.classList.add('text-success');
                else if(data.ping <= 50) pl.classList.add('text-warning');
                else pl.classList.add('text-danger');
                
                setTimeout(() => location.reload(), 3000);
            } else {
                alert("Speed test failed: " + data.error);
            }
        }).catch(err => {
            loader.classList.add('d-none');
            alert("Error running speed test.");
        });
}

// Admin API calls
function loadUsers() {
    fetch('/admin/users').then(res=>res.json()).then(users => {
        let html = '';
        users.forEach(u => {
            html += `<tr>
                <td>${u.id}</td>
                <td>${u.name} ${u.is_admin ? '<span class="badge" style="background:var(--primary);color:white;">Admin</span>' : ''}</td>
                <td>${u.email}</td>
                <td>${u.created_at.split(' ')[0]}</td>
                <td>${u.total_scans}</td>
                <td>${u.last_scan || 'Never'}</td>
                <td>${!u.is_admin ? `<button class="btn btn-secondary text-danger" style="padding:4px 8px;" onclick="adminDeleteUser(${u.id})">Delete</button>` : ''}</td>
            </tr>`;
        });
        document.getElementById('usersBody').innerHTML = html;
    });
}

function loadAllReports() {
    fetch('/admin/reports').then(res=>res.json()).then(reports => {
        let html = '';
        reports.forEach(r => {
            html += `<tr>
                <td>${r.id}</td>
                <td>${r.user_name}</td>
                <td>${r.scan_date}</td>
                <td>${r.cpu_usage}%</td>
                <td>${r.ram_usage}%</td>
                <td>${r.disk_usage}%</td>
                <td><span class="badge" style="background:var(--primary);color:white;">${r.security_score}</span></td>
                <td>
                    <button class="btn btn-secondary text-danger" style="padding:4px 8px;" onclick="deleteReport(${r.id})">Delete</button>
                </td>
            </tr>`;
        });
        document.getElementById('reportsBody').innerHTML = html;
    });
}

function adminDeleteUser(id) {
    if(confirm("Delete this user and ALL their data?")) {
        fetch(`/admin/user/${id}`, {method:'DELETE'}).then(res=>res.json()).then(d => {
            if(d.success) loadUsers();
        });
    }
}

function deleteReport(id) {
    if(confirm("Are you sure you want to delete this report?")) {
        fetch(`/report/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => { if(data.success) location.reload(); });
    }
}

function viewOldReport(id) {
    alert("Functionality to view old report detail can be expanded here.");
}

// Initialization for Dashboard
document.addEventListener("DOMContentLoaded", () => {
    
    // Normal Dashboard initialization
    if (typeof lastScanRaw !== 'undefined' && lastScanRaw) {
        // Metrics
        setTimeout(() => {
            animateCounter(document.getElementById('metric-cpu'), lastScanRaw.cpu_usage, '%');
            updateColor('metric-cpu', lastScanRaw.cpu_usage);
            animateCounter(document.getElementById('metric-ram'), lastScanRaw.ram_usage, '%');
            updateColor('metric-ram', lastScanRaw.ram_usage);
            animateCounter(document.getElementById('metric-disk'), lastScanRaw.disk_usage, '%');
            updateColor('metric-disk', lastScanRaw.disk_usage);
        }, 500);

        // Populate Issues List
        const issuesContainer = document.getElementById('issues-list');
        const issues = JSON.parse(lastScanRaw.issues_found);
        const fixes = JSON.parse(lastScanRaw.fixes_suggested);
        
        if(issues.length === 0) {
            issuesContainer.innerHTML = '<p class="text-success" style="padding:10px;"><i class="fas fa-check-circle"></i> No issues found. System is healthy!</p>';
        } else {
            let html = '';
            issues.forEach((issue, idx) => {
                html += `<div class="issue-item">
                    <span class="issue-title"><i class="fas fa-exclamation-circle"></i> ${issue}</span>
                    <span class="issue-fix">Fix: ${fixes[idx]}</span>
                </div>`;
            });
            issuesContainer.innerHTML = html;
        }

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
                // Determine priority
                let priorityClass = 'bg-low';
                let priorityText = 'Low';
                let icon = 'fa-info-circle';
                
                if(issue.includes("Critical") || issue.includes("Disconnected")) {
                    priorityClass = 'bg-high'; priorityText = 'High'; icon = 'fa-times-circle';
                } else if(issue.includes("Warning")) {
                    priorityClass = 'bg-medium'; priorityText = 'Medium'; icon = 'fa-exclamation-triangle';
                }

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

        // Render User Charts
        renderUserCharts(lastScanRaw, allReports);

        // Render Device Information
        renderDeviceInfo(lastScanRaw);
    }

    // Render Admin Charts if on admin panel
    if (typeof adminStats !== 'undefined' && adminStats) {
        renderAdminCharts(adminStats);
    }
    
    // Render Speed test charts
    if (typeof speedTests !== 'undefined' && speedTests.length > 0) {
        renderSpeedTestChart(speedTests);
    }

    // Badge styling for History Table
    document.querySelectorAll('.cpu-color-bg, .ram-color-bg, .disk-color-bg').forEach(el => {
        let val = parseFloat(el.innerText);
        if(val<60) { el.style.background = 'rgba(0,255,136,0.2)'; el.style.color = '#00aa55'; }
        else if(val<80) { el.style.background = 'rgba(255,215,0,0.2)'; el.style.color = '#ccaa00'; }
        else { el.style.background = 'rgba(255,68,68,0.2)'; el.style.color = '#ff4444'; }
    });
});

function createDonut(ctxId, label, value, color) {
    const ctx = document.getElementById(ctxId);
    if(!ctx) return;
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: [label, 'Empty'],
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [color, COLORS.empty],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '75%',
            plugins: { 
                datalabels: { display: false },
                legend: { display: true, position: 'bottom', labels: { color: '#1F2937' } },
                tooltip: { callbacks: { label: function(context) { return context.label + ': ' + context.parsed + '%'; } } }
            }
        }
    });
}

function renderUserCharts(current, history) {
    Chart.defaults.color = '#1F2937';
    
    // Donuts unchanged (except datalabels disabled)
    createDonut('cpuDonut', 'CPU', current.cpu_usage, COLORS.cpu);
    createDonut('ramDonut', 'RAM', current.ram_usage, COLORS.ram);
    createDonut('diskDonut', 'Disk', current.disk_usage, COLORS.disk);

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
                    scales: {
                        y: { max: 100, min: 0, grid: { color: '#E5E7EB' } },
                        x: { grid: { display: false } }
                    },
                    plugins: {
                        legend: { display: true, position: 'top' },
                        datalabels: {
                            color: '#1F2937',
                            anchor: 'end',
                            align: 'top',
                            formatter: Math.round,
                            font: { size: 10 }
                        }
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
        let secStatus = "Critical"; let statColor = "#ff4444";
        if(current.security_score > 40) { secStatus = "Needs Attention"; statColor = "#ffd700"; }
        if(current.security_score > 70) { secStatus = "Good"; statColor = "#7C3AED"; }
        if(current.security_score > 90) { secStatus = "Excellent"; statColor = "#00ff88"; }
        document.getElementById('secStatusText').innerText = `Status: ${secStatus}`;
        document.getElementById('secStatusText').style.color = statColor;

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
                scales: {
                    x: { max: 20, grid: { color: '#E5E7EB' } },
                    y: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        color: '#1F2937',
                        anchor: 'end',
                        align: 'right',
                        formatter: function(val) { return val + " pts"; },
                        font: { weight: 'bold' }
                    }
                }
            }
        });
    }
}

function renderSpeedTestChart(st) {
    const stRev = [...st].reverse();
    const ctx = document.getElementById('speedTestBarChart');
    if(ctx) {
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stRev.map(h => h.test_date + ' ' + h.test_time),
                datasets: [
                    { label: 'Download (Mbps)', data: stRev.map(h => h.download_speed), backgroundColor: '#7C3AED', borderRadius: 4 },
                    { label: 'Upload (Mbps)', data: stRev.map(h => h.upload_speed), backgroundColor: '#EC4899', borderRadius: 4 },
                    { label: 'Ping (ms)', data: stRev.map(h => h.ping), backgroundColor: '#A78BFA', borderRadius: 4 }
                ]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                scales: { y: { grid: { color: '#E5E7EB' } }, x: { grid: { display: false } } },
                plugins: {
                    legend: { display: true },
                    datalabels: {
                        color: '#1F2937',
                        anchor: 'end',
                        align: 'top',
                        formatter: Math.round,
                        font: { size: 10 }
                    }
                }
            }
        });
    }
}

function getStorageBarColor(pct) {
    if (pct >= 91) return '#EF4444';
    if (pct >= 81) return '#EC4899';
    if (pct >= 61) return '#A78BFA';
    return '#7C3AED';
}

function deviceRow(label, value) {
    return `<div class="device-info-row">
        <span class="device-info-label">${label}</span>
        <span class="device-info-value">${value ?? 'N/A'}</span>
    </div>`;
}

function buildSubCard(icon, title, rowsHtml) {
    return `<div class="device-sub-card">
        <div class="device-sub-card-header">${icon} ${title}</div>
        <div class="device-sub-card-body">${rowsHtml}</div>
    </div>`;
}

function renderDeviceInfo(scan) {
    const container = document.getElementById('device-info-container');
    if (!container) return;

    let info = null;
    try {
        if (scan.device_info) {
            info = typeof scan.device_info === 'string' ? JSON.parse(scan.device_info) : scan.device_info;
        }
    } catch (e) { info = null; }

    if (!info) {
        container.innerHTML = `<div class="no-data-card"><p>Run a new scan to collect detailed device information.</p></div>`;
        return;
    }

    const dev = info.device || {};
    const os = info.os || {};
    const proc = info.processor || {};
    const gpu = info.gpu || {};
    const ram = info.ram || {};
    const storage = info.storage || [];
    const network = info.network || [];

    const isLaptop = dev.device_type && dev.device_type.includes('Laptop');

    let deviceRows = deviceRow('Hostname', dev.hostname) +
        deviceRow('Device Type', dev.device_type);
    if (isLaptop) {
        deviceRows += deviceRow('Battery', dev.battery_percent) +
            deviceRow('Battery Status', dev.battery_status) +
            deviceRow('Battery Health', dev.battery_health);
    }
    deviceRows += deviceRow('System Uptime', dev.uptime) +
        deviceRow('Last Boot Time', dev.last_boot_time) +
        deviceRow('BIOS Version', dev.bios_version) +
        deviceRow('OS', os.full_name) +
        deviceRow('OS Version', os.version) +
        deviceRow('Build Number', os.build) +
        deviceRow('Architecture', os.architecture) +
        deviceRow('Activation', os.activation) +
        deviceRow('Last Update', os.last_update) +
        deviceRow('Language', os.language);

    const deviceOverview = buildSubCard('💻', 'Device Overview', deviceRows);

    const processorCard = buildSubCard('⚙️', 'Processor Details',
        deviceRow('Processor', proc.name) +
        deviceRow('Generation', proc.generation) +
        deviceRow('Brand', proc.brand) +
        deviceRow('Physical Cores', proc.physical_cores) +
        deviceRow('Logical Cores', proc.logical_cores) +
        deviceRow('Current Speed', proc.current_speed) +
        deviceRow('Max Speed', proc.max_speed) +
        deviceRow('Architecture', proc.architecture)
    );

    const gpuCard = buildSubCard('🎮', 'GPU Details',
        deviceRow('GPU', gpu.name) +
        deviceRow('Brand', gpu.brand) +
        deviceRow('VRAM', gpu.vram) +
        deviceRow('GPU Usage', gpu.usage) +
        deviceRow('Resolution', gpu.resolution) +
        deviceRow('Displays', gpu.display_count)
    );

    let storageHtml = '';
    if (storage.length === 0) {
        storageHtml = buildSubCard('💾', 'Storage Details', deviceRow('Drives', 'N/A'));
    } else {
        storage.forEach(drive => {
            const pct = drive.usage_percent || 0;
            const barColor = getStorageBarColor(pct);
            const driveLabel = drive.letter + (drive.name && drive.name !== drive.letter ? ` (${drive.name})` : '');
            storageHtml += `<div class="device-sub-card">
                <div class="device-sub-card-header">💾 Storage — ${driveLabel}</div>
                <div class="device-sub-card-body">
                    ${deviceRow('Total', drive.total_fmt)}
                    ${deviceRow('Used', drive.used_fmt)}
                    ${deviceRow('Free', drive.free_fmt)}
                    ${deviceRow('Drive Type', drive.type)}
                    <div class="storage-bar-container">
                        <div class="storage-bar-header">
                            <span class="storage-bar-label">Usage</span>
                            <span class="storage-bar-pct">${pct}%</span>
                        </div>
                        <div class="storage-bar-track">
                            <div class="storage-bar-fill" style="width:${pct}%; background:${barColor};"></div>
                        </div>
                        <div class="storage-bar-caption">${drive.used_fmt} / ${drive.total_fmt}</div>
                    </div>
                </div>
            </div>`;
        });
    }

    const ramBarColor = getStorageBarColor(ram.usage_percent || 0);
    const ramCard = buildSubCard('🧠', 'RAM Details',
        deviceRow('Total RAM', ram.total_fmt) +
        deviceRow('Used RAM', ram.used_fmt) +
        deviceRow('Free RAM', ram.free_fmt) +
        deviceRow('RAM Type', ram.type) +
        deviceRow('RAM Speed', ram.speed) +
        `<div class="device-info-row">
            <span class="device-info-label">Usage</span>
            <span class="device-info-value">${ram.usage_percent ?? 'N/A'}%</span>
        </div>
        <div style="padding: 0 20px 12px;">
            <div class="ram-usage-bar-track">
                <div class="ram-usage-bar-fill" style="width:${ram.usage_percent || 0}%; background:${ramBarColor};"></div>
            </div>
        </div>`
    );

    let networkHtml = '';
    if (network.length === 0) {
        networkHtml = buildSubCard('🌐', 'Network Adapters', deviceRow('Adapters', 'N/A'));
    } else {
        let adapterRows = '';
        network.forEach((adapter, idx) => {
            adapterRows += `<div class="network-adapter-block">
                ${deviceRow('Adapter', adapter.name)}
                ${deviceRow('IP Address', adapter.ip)}
                ${deviceRow('MAC Address', adapter.mac)}
                ${deviceRow('Connection', adapter.connection_type)}
                ${deviceRow('Speed', adapter.speed)}
            </div>`;
        });
        networkHtml = buildSubCard('🌐', 'Network Adapters', adapterRows);
    }

    container.innerHTML = `
        <div class="device-info-col">
            ${deviceOverview}
            ${processorCard}
            ${gpuCard}
        </div>
        <div class="device-info-col">
            ${storageHtml}
            ${ramCard}
            ${networkHtml}
        </div>
    `;
}

function renderAdminCharts(stats) {
    Chart.defaults.color = '#1F2937';
    
    const ctxBar = document.getElementById('adminBarChart');
    if(ctxBar && stats.scans_per_day) {
        new Chart(ctxBar.getContext('2d'), {
            type: 'bar',
            data: {
                labels: stats.scans_per_day.map(s => s.scan_date),
                datasets: [{ label: 'Scans', data: stats.scans_per_day.map(s => s.count), backgroundColor: '#7C3AED', borderRadius: 4 }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                plugins: { datalabels: { color: '#1F2937', anchor: 'end', align: 'top' } }
            }
        });
    }

    const ctxLine = document.getElementById('adminLineChart');
    if(ctxLine && stats.avg_scores) {
        new Chart(ctxLine.getContext('2d'), {
            type: 'line',
            data: {
                labels: stats.avg_scores.map(s => s.scan_date),
                datasets: [{ label: 'Avg Score', data: stats.avg_scores.map(s => s.avg_score), borderColor: '#EC4899', fill: true, backgroundColor: 'rgba(236,72,153,0.2)', tension: 0.4 }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } },
                plugins: { datalabels: { display: false } }
            }
        });
    }
}
