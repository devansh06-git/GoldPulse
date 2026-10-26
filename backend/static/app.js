const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

let processedData = [];
let termChartInstance = null;
let devChartInstance = null;
let backtestChartInstance = null;

// Initialize Lucide Icons on load
window.onload = function() {
    lucide.createIcons();
    loadSampleData();
};

// Toast Notifications
function showToast(message, isError = false) {
    const toast = document.getElementById('toastNotification');
    const msgEl = document.getElementById('toastMessage');
    const iconEl = document.getElementById('toastIcon');

    msgEl.innerText = message;
    if (isError) {
        toast.firstElementChild.className = "flex items-center gap-3 px-4 py-3 rounded-lg bg-panelbg border border-rose-500/40 text-slate-100 shadow-2xl text-xs font-mono";
        iconEl.setAttribute('data-lucide', 'alert-triangle');
        iconEl.className = "w-4 h-4 text-rose-400";
    } else {
        toast.firstElementChild.className = "flex items-center gap-3 px-4 py-3 rounded-lg bg-panelbg border border-accentcyan/40 text-slate-100 shadow-2xl text-xs font-mono";
        iconEl.setAttribute('data-lucide', 'check-circle');
        iconEl.className = "w-4 h-4 text-emerald-400";
    }
    lucide.createIcons();

    toast.classList.remove('opacity-0', 'translate-y-20');
    toast.classList.add('opacity-100', 'translate-y-0');

    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'translate-y-20');
    }, 3500);
}

// Upload CSV file directly to FastAPI backend
async function parseCSVFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        showToast("Uploading CSV to Python Backend API...");
        const response = await fetch(`${API_BASE_URL}/normalize`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to process CSV file");
        }

        processedData = await response.json();
        
        if (processedData.length === 0) {
            showToast("No valid MCX Gold contracts found in file.", true);
            renderTable([]);
            return;
        }

        document.getElementById('activeFileStatus').innerHTML = `Active Dataset: <span class="text-accentcyan font-mono">${file.name} (${processedData.length} rows)</span>`;
        
        updateKPICards();
        renderTable(processedData);
        renderCharts(processedData);
        triggerBacktestAPI();
        showToast(`Processed ${processedData.length} contracts via Python engine!`);

    } catch (err) {
        showToast(`API Error: ${err.message}`, true);
    }
}

// Trigger Walk-Forward Backtest API
async function triggerBacktestAPI() {
    if (processedData.length === 0) return;

    try {
        const response = await fetch(`${API_BASE_URL}/backtest`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(processedData)
        });

        if (response.ok) {
            const backtestRes = await response.json();
            renderBacktestChart(backtestRes);
        }
    } catch (err) {
        console.error("Backtest API error:", err);
    }
}

// Render Table Rows
function renderTable(data) {
    const tbody = document.getElementById('contractsTableBody');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="p-6 text-center text-steel font-sans">No matching contracts found. Click "Upload CSV" or "Load Sample Bhavcopy".</td></tr>`;
        return;
    }

    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/40 transition border-b border-slate-800/40";

        let signalBadge = '';
        if (row.signal === 'OVERPRICED') {
            signalBadge = `<span class="px-2 py-1 text-xs rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">OVERPRICED (SHORT)</span>`;
        } else if (row.signal === 'UNDERPRICED') {
            signalBadge = `<span class="px-2 py-1 text-xs rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">UNDERPRICED (LONG)</span>`;
        } else if (row.signal === 'THIN LIQUIDITY') {
            signalBadge = `<span class="px-2 py-1 text-xs rounded-md bg-slate-800 text-steel border border-slate-700 font-semibold">THIN LIQUIDITY</span>`;
        } else {
            signalBadge = `<span class="px-2 py-1 text-xs rounded-md bg-accentcyan/10 text-accentcyan border border-accentcyan/20 font-semibold">QUIET / NEUTRAL</span>`;
        }

        const devColor = row.devPct > 0 ? 'text-rose-400' : (row.devPct < 0 ? 'text-emerald-400' : 'text-slate-300');

        tr.innerHTML = `
            <td class="p-3 font-bold text-white">${row.SYMBOL}</td>
            <td class="p-3 text-slate-300">${row.EXPIRY_DT}</td>
            <td class="p-3 text-steel">${row.PURITY} Fineness</td>
            <td class="p-3 text-slate-200">₹${row.CLOSE.toLocaleString()}</td>
            <td class="p-3 font-semibold text-accentcyan">₹${row.norm1gPrice.toFixed(2)}</td>
            <td class="p-3 text-slate-300">₹${row.benchmark.toFixed(2)}</td>
            <td class="p-3 font-bold ${devColor}">${row.devPct > 0 ? '+' : ''}${row.devPct.toFixed(2)}%</td>
            <td class="p-3 text-slate-300">${row.VOLUME.toLocaleString()}</td>
            <td class="p-3 text-center">${signalBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Render Backtest Equity Curve Chart from API Response
function renderBacktestChart(backtestRes) {
    const labels = backtestRes.equityCurve.map(p => p.month);
    const strategyData = backtestRes.equityCurve.map(p => p.strategyEquity);
    const benchmarkData = backtestRes.equityCurve.map(p => p.benchmarkEquity);

    if (backtestChartInstance) backtestChartInstance.destroy();
    const ctx = document.getElementById('backtestChart').getContext('2d');
    backtestChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'MCX RV Quant Strategy (Net)',
                    data: strategyData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2
                },
                {
                    label: 'Underlying Gold Price Benchmark',
                    data: benchmarkData,
                    borderColor: '#64748b',
                    borderDash: [4, 4],
                    fill: false,
                    tension: 0.3,
                    borderWidth: 1.5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
                y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } }
            }
        }
    });
}