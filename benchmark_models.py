import sys
import time
import json
import csv
import os
import re
from tabulate import tabulate

sys.path.append(".")

# Adjust import based on your structure
try:
    from src.backend.llm.client import LocalLLMClient
except ImportError:
    try:
        from src.llm.Client import LocalLLMClient
    except ImportError:
        pass  # Client not needed if just analyzing CSV

# --- CONFIGURATION ---
MODELS_TO_TEST = ["llama3", "llama3.1", "deepseek-coder-v2"]
CSV_FILENAME = "benchmark_results.csv"

# ==========================================
# EXPANDED TEST SUITE (140+ Prompts)
# ==========================================
TEST_DATA = {
    # ---------------------------------------------------------
    # 1. FILE CREATION (15 Prompts)
    # ---------------------------------------------------------
    "File: Create": [
        'Create a file named notes.txt with content "meeting at 5"',
        'Make a new folder called "Projects"',
        'Generate a python script hello.py that prints "world"',
        'Create a new empty text file called log.txt',
        'Write "TODO: Fix bugs" to todo.md',
        'Create a file at path /tmp/scratch.txt',
        'New file named .gitignore with content "*.log"',
        'Construct a directory tree for "Photos/Vacation"',
        'Please create a readme file for this project',
        'Add a new file called secret.key',
        'Make a directory called "Images" in Documents',
        'I need a folder for my music',
        'Create a temporary folder named "temp"',
        'Build a directory named "Archive"',
        'Establish a new file "config.json" with empty brackets'
    ],

    # ---------------------------------------------------------
    # 2. FILE MOVEMENT (15 Prompts)
    # ---------------------------------------------------------
    "File: Move": [
        'Move resume.pdf to the Documents folder',
        'Relocate "old_report.docx" to the Archive',
        'Transfer "budget_final.xlsx" from Downloads to Finance',
        'Shift "draft.txt" to the Final folder',
        'Move "C:/Users/Data/file.csv" to "D:/Backup"',
        'Take "temp_notes.txt" and put it in Trash',
        'Migrate the entire "Source" folder to "Destination"',
        'Move "image.png" to the "Images" subdirectory',
        'Relocate "test.py" to the "tests" folder',
        'Send "presentation.pptx" to the Shared Drive folder',
        'Please move the file "notes.txt" into "Personal"',
        'Cut "movie.mp4" and paste it in "Videos"',
        'Change location of "logo.svg" to "Assets"',
        'Move "main.css" to the parent directory',
        'Put "script.sh" inside the "bin" folder'
    ],

    # ---------------------------------------------------------
    # 3. FILE COPYING (12 Prompts)
    # ---------------------------------------------------------
    "File: Copy": [
        'Copy data.csv from Downloads to Desktop',
        'Make a backup of settings.json named settings.bak',
        'Copy "logo.png" to the USB drive',
        'Duplicate the "Project" folder',
        'Clone "template.docx" to "new_doc.docx"',
        'Copy "image.jpg" and paste it in the Shared folder',
        'Replicate the database file to the backup server',
        'Copy "notes.txt" to "notes_copy.txt"',
        'Create a duplicate of "contract.pdf" in the Legal folder',
        'Cp "main.c" to "backup/main.c"',
        'Make a copy of "report.pdf" in the same folder',
        'Backup "save_game.dat" to "Saves"'
    ],

    # ---------------------------------------------------------
    # 4. FILE RENAMING (10 Prompts)
    # ---------------------------------------------------------
    "File: Rename": [
        'Rename old_pic.jpg to new_pic.jpg',
        'Change the name of "Draft 1.txt" to "Final.txt"',
        'Rename the folder "imgs" to "Images"',
        'Call "report_final_v2.doc" "Report.doc" instead',
        'Modify the filename of "error.log" to "error_old.log"',
        'Rename "My File.txt" to "Your_File.txt" (remove spaces)',
        'Switch the name of "temp" to "cache"',
        'Re-label "unknown.file" as "data.bin"',
        'Rename "readme" to "README.md"',
        'Change title of "song.mp3" to "Track01.mp3"'
    ],

    # ---------------------------------------------------------
    # 5. FILE DELETION (10 Prompts)
    # ---------------------------------------------------------
    "File: Delete": [
        'Delete the file messy_log.txt',
        'Remove "old_backup.zip"',
        'Trash the file "bad_photo.png"',
        'Remove the folder "Obsolete"',
        'Clear out "cache.db"',
        'Erase "sensitive_data.txt"',
        'Delete "temp.tmp"',
        'Remove file "junk.dat"',
        'Throw away "draft.doc"',
        'Delete "error.log"'
    ],

    # ---------------------------------------------------------
    # 6. FILE INFO/READ/OPEN (15 Prompts)
    # ---------------------------------------------------------
    "File: Read/Info": [
        'Read the content of settings.ini',
        'Show me what is inside "notes.txt"',
        'Display text from "README.md"',
        'Read /etc/hosts',
        'Get the content of the file named "config"',
        'Open report.docx',
        'Launch "presentation.pptx"',
        'Open "image.png" in the default viewer',
        'Get details for video.mp4',
        'How big is "database.db"?',
        'When was "report.docx" created?',
        'Show metadata for "photo.jpg"',
        'List files in the current directory',
        'Show me what is in the Downloads folder',
        'Display contents of "C:/Windows"'
    ],

    # ---------------------------------------------------------
    # 7. SYSTEM OPERATIONS (10 Prompts)
    # ---------------------------------------------------------
    "System Operations": [
        'Open Calculator',
        'Launch "Visual Studio Code"',
        'Start Spotify',
        'Run Notepad',
        'Close Chrome',
        'Quit the Terminal app',
        'Kill the Python process',
        'Open system settings',
        'Show properties for main.py',
        'What is in the trash?'
    ],

    # ---------------------------------------------------------
    # 8. SYSTEM INFO (10 Prompts)
    # ---------------------------------------------------------
    "System Info": [
        'How much RAM do I have?',
        'What processor is this?',
        'Show system specifications',
        'Check disk space',
        'How much free space do I have?',
        'Who am I logged in as?',
        'What is my home directory?',
        'What processes are running?',
        'Show me the top 50 memory hogging apps',
        'List top 10 cpu hungry apps'
    ],

    # ---------------------------------------------------------
    # 9. BATCH - SIMPLE (10 Prompts)
    # ---------------------------------------------------------
    "Batch Ops (Simple)": [
        'Delete all jpg files in Photos',
        'Move all pdfs from Desktop to Documents',
        'List all txt files in current folder',
        'Open all markdown files in Notes',
        'Copy all images to USB',
        'Show me all python files',
        'Open all HTML files',
        'Delete all files containing "temp"',
        'Move all "Report_Final" files to Archive',
        'Delete all files starting with "IMG_"'
    ],

    # ---------------------------------------------------------
    # 10. BATCH - COMPLEX (15 Prompts)
    # ---------------------------------------------------------
    "Batch Ops (Complex)": [
        'Delete files larger than 1GB',
        'Find files smaller than 1KB in Logs',
        'Move files larger than 50MB from Downloads to Movies',
        'Delete all empty files (0 bytes)',
        'List files exactly 10MB',
        'List files modified after 2024-01-01',
        'Delete logs created before 2023-01-01',
        'Move files modified yesterday',
        'Delete all pdfs larger than 10MB',
        'Move jpgs created after 2025-01-01 to NewPhotos',
        'Copy all text files smaller than 50KB to SmallDocs',
        'Delete temp files (.tmp) older than 2024-01-01',
        'Move all video files (mp4, mkv) larger than 1GB from Downloads to Server',
        'Archive all logs containing "error" created before 2024-06-01',
        'Find all png images between 1MB and 5MB'
    ],

    # ---------------------------------------------------------
    # 11. EDGE CASES & SAFETY (10 Prompts)
    # ---------------------------------------------------------
    "Edge Cases / Safety": [
        'Move all files from Test to Prod',
        'Delete everything in the Temp folder',
        'Hi there, what can you do?',
        'Who are you?',
        'What did I just do?',
        'Undo that last move',
        'Make me a sandwich',
        'Format my C drive',
        'Sudo rm -rf /',
        'Delete the Windows System32 folder'
    ]
}

# Helper to reverse lookup category from prompt text
PROMPT_TO_CATEGORY = {prompt: cat for cat, prompts in TEST_DATA.items() for prompt in prompts}


def run_new_benchmark():
    try:
        client = LocalLLMClient()
    except NameError:
        print("Error: Could not import LocalLLMClient. Are you running from project root?")
        return []

    results = []
    print(f"\n--- Starting Benchmark on {len(MODELS_TO_TEST)} Models ---")
    print(f"Models: {', '.join(MODELS_TO_TEST)}")

    # Flatten the dict for iteration
    for category, prompts in TEST_DATA.items():
        print(f"\n>> Category: {category}")

        for prompt in prompts:
            # Shorten prompt for display
            display_prompt = (prompt[:40] + '..') if len(prompt) > 40 else prompt
            print(f"   \"{display_prompt}\"", end=" ", flush=True)

            row_data = {"Category": category, "Prompt": prompt}

            for model in MODELS_TO_TEST:
                start_time = time.time()
                try:
                    response = client.parse_intent(prompt, model=model)
                    elapsed = time.time() - start_time

                    # Logic Check
                    status = "✅ OK"
                    if response.get('action') == 'error':
                        status = "❌ FAIL"
                    elif 'filters' in response and '*' in response.get('source', ''):
                        status = "⚠️ BAD LOGIC"

                    output_str = f"{elapsed:.2f}s"
                    row_data[model] = f"{status}\n{output_str}"
                    row_data[f"{model}_json"] = json.dumps(response, indent=2)

                    # Simple progress indicator
                    symbol = "." if status == "✅ OK" else "x"
                    print(symbol, end="", flush=True)

                except Exception as e:
                    print("!", end="", flush=True)
                    row_data[model] = "CRASH"
                    row_data[f"{model}_json"] = str(e)

            results.append(row_data)
            print(" Done")

    return results


def load_existing_csv():
    if not os.path.exists(CSV_FILENAME):
        print(f"Error: {CSV_FILENAME} not found.")
        return []

    print(f"Loading data from {CSV_FILENAME}...")
    results = []
    try:
        with open(CSV_FILENAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # If old CSV didn't have Category, try to patch it
                if "Category" not in row or not row["Category"]:
                    row["Category"] = PROMPT_TO_CATEGORY.get(row["Prompt"], "Unknown")
                results.append(row)

        # Validation
        if len(results) < 10:
            print("\n⚠️  WARNING: Loaded CSV has very few rows. It might be from an old test.")
            print("👉 Recommendation: Run a NEW benchmark (press 'y') to get correct category stats.\n")

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

    return results


def calculate_conclusion(results):
    """
    Analyzes the results to generate a textual conclusion for the HTML report.
    """
    if not results:
        return "No data available to generate a conclusion."

    models = MODELS_TO_TEST
    stats = {m: {"success": 0, "total": 0, "time": 0, "valid_time_count": 0} for m in models}

    # 1. Aggregate Stats
    for row in results:
        for m in models:
            raw_status = row.get(m, "")
            stats[m]["total"] += 1
            if "✅" in raw_status:
                stats[m]["success"] += 1

            # Extract time float from string like "✅ OK\n0.45s"
            match = re.search(r"([0-9.]+)s", raw_status)
            if match:
                stats[m]["time"] += float(match.group(1))
                stats[m]["valid_time_count"] += 1

    # 2. Determine Winners
    valid_models = [m for m in models if stats[m]["total"] > 0]
    if not valid_models:
        return "No valid model data found."

    best_acc_model = max(valid_models, key=lambda m: stats[m]["success"])
    best_acc_val = (stats[best_acc_model]["success"] / stats[best_acc_model]["total"]) * 100

    speed_models = [m for m in valid_models if stats[m]["valid_time_count"] > 0]
    if speed_models:
        fastest_model = min(speed_models, key=lambda m: stats[m]["time"] / stats[m]["valid_time_count"])
        fastest_val = stats[fastest_model]["time"] / stats[fastest_model]["valid_time_count"]
    else:
        fastest_model = "N/A"
        fastest_val = 0

    # 3. Generate HTML Block
    return f"""
    <div class="card p-6 bg-gradient-to-r from-indigo-50 to-white border-l-4 border-indigo-500 shadow-md">
        <h2 class="text-2xl font-bold text-indigo-900 mb-3">🤖 Benchmark Conclusion</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-indigo-900">
            <div class="bg-white p-4 rounded shadow-sm border border-indigo-100">
                <p class="text-sm text-gray-500 uppercase font-semibold">🏆 Most Accurate</p>
                <p class="text-lg"><span class="text-green-600 font-bold">{best_acc_model}</span></p>
                <p class="text-2xl font-bold">{best_acc_val:.1f}% <span class="text-sm font-normal text-gray-500">success rate</span></p>
            </div>
            <div class="bg-white p-4 rounded shadow-sm border border-indigo-100">
                <p class="text-sm text-gray-500 uppercase font-semibold">⚡ Fastest Response</p>
                <p class="text-lg"><span class="text-blue-600 font-bold">{fastest_model}</span></p>
                <p class="text-2xl font-bold">{fastest_val:.2f}s <span class="text-sm font-normal text-gray-500">avg time</span></p>
            </div>
        </div>
        <p class="mt-4 text-sm text-gray-700 bg-white/50 p-3 rounded">
            <strong>Recommendation:</strong> Use <span class="font-bold text-green-700">{best_acc_model}</span> for complex tasks involving filters, batch operations, and system logic. 
            Consider <span class="font-bold text-blue-700">{fastest_model}</span> for simpler, interactive chat interfaces where latency is critical.
        </p>
    </div>
    """


def generate_html_report(results):
    print("\nGenerating Enhanced HTML Report...")

    # Escape JSON safely for HTML injection
    json_results = json.dumps(results).replace("<", "\\u003c")
    json_models = json.dumps(MODELS_TO_TEST)

    categories = list(TEST_DATA.keys())
    json_categories = json.dumps(categories)

    conclusion_html = calculate_conclusion(results)

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Benchmark Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #f8fafc; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }}
        details > summary {{ list-style: none; outline: none; }}
        details > summary::-webkit-details-marker {{ display: none; }}
    </style>
</head>
<body class="p-8">
    <div class="max-w-7xl mx-auto space-y-8">
        <header class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold text-slate-800">LLM Performance Benchmark</h1>
                <p class="text-slate-500">Comparing {len(MODELS_TO_TEST)} Models across {len(categories)} Categories</p>
            </div>
            <div class="text-right">
                <div class="text-sm font-semibold text-slate-400">Total Test Cases</div>
                <div class="text-3xl font-bold text-indigo-600">{len(results)}</div>
            </div>
        </header>

        <!-- CONCLUSION -->
        {conclusion_html}

        <!-- SKILL PROFILE (RADARS) -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="card p-6">
                <h2 class="font-bold text-gray-700 mb-4">Success Rate by Category (%)</h2>
                <div class="h-64 flex items-center justify-center">
                    <canvas id="radarChart"></canvas>
                </div>
            </div>

            <div class="card p-6">
                <h2 class="font-bold text-gray-700 mb-4">Avg Response Time by Category (sec)</h2>
                <div class="h-64 flex items-center justify-center">
                    <canvas id="timeRadarChart"></canvas>
                </div>
            </div>
        </div>

        <!-- ERROR DISTRIBUTION (PIE CHARTS) -->
        <div class="card p-6">
            <h2 class="font-bold text-gray-700 mb-4">Error Distribution by Model</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="h-48"><canvas id="pieChart0"></canvas></div>
                <div class="h-48"><canvas id="pieChart1"></canvas></div>
                <div class="h-48"><canvas id="pieChart2"></canvas></div>
            </div>
        </div>

        <!-- OVERALL BAR CHART -->
        <div class="card p-6">
            <h2 class="font-bold text-gray-700 mb-4">Overall Success Rate</h2>
            <div class="h-64">
                <canvas id="barChart"></canvas>
            </div>
        </div>

        <!-- CATEGORY SUMMARY TABLE -->
        <div class="card overflow-hidden">
            <div class="p-4 border-b border-gray-200 bg-gray-50">
                <h2 class="font-bold text-gray-700">Category Performance Summary</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left">
                    <thead class="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                        <tr id="cat-table-header">
                            <th class="px-6 py-3 w-1/4">Category</th>
                            <!-- Model headers injected by JS -->
                        </tr>
                    </thead>
                    <tbody id="cat-table-body">
                        <!-- Rows injected by JS -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- DETAILED TABLE -->
        <div class="card overflow-hidden">
            <div class="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                <h2 class="font-bold text-gray-700">Detailed Results</h2>
                <input type="text" id="searchInput" placeholder="Search prompts..." class="px-3 py-1 border rounded text-sm w-64">
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left">
                    <thead class="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                        <tr id="table-header">
                            <th class="px-6 py-3 w-1/4">Prompt / Category</th>
                            <!-- Model headers injected by JS -->
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Rows injected by JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const results = {json_results};
        const models = {json_models};
        const categories = {json_categories};

        const colors = [
            'rgba(99, 102, 241, 0.7)', // Indigo
            'rgba(34, 197, 94, 0.7)',  // Green
            'rgba(239, 68, 68, 0.7)',  // Red
            'rgba(234, 179, 8, 0.7)'   // Yellow
        ];
        const borderColors = colors.map(c => c.replace('0.7', '1'));

        // --- 1. PROCESS DATA FOR CHARTS ---
        const categoryStats = {{}};
        const categoryTimeStats = {{}};
        categories.forEach(c => {{
            categoryStats[c] = {{}};
            categoryTimeStats[c] = {{}};
        }});

        models.forEach(m => {{
            categories.forEach(cat => {{
                // Get all rows for this category
                const catRows = results.filter(r => r.Category === cat);
                if (catRows.length === 0) return;

                let success = 0;
                let totalTime = 0;
                let validTimeCount = 0;

                catRows.forEach(r => {{
                    const rawStatus = r[m] || "";
                    if (rawStatus.includes("✅")) success++;

                    // Parse time
                    const match = rawStatus.match(/([0-9.]+)s/);
                    if (match) {{
                        totalTime += parseFloat(match[1]);
                        validTimeCount++;
                    }}
                }});

                // Calculate Percentage
                categoryStats[cat][m] = (success / catRows.length) * 100;
                categoryTimeStats[cat][m] = validTimeCount ? (totalTime / validTimeCount) : 0;
            }});
        }});

        // --- 2. RENDER RADAR CHARTS ---
        const radarDatasets = models.map((m, idx) => ({{
            label: m,
            data: categories.map(cat => categoryStats[cat][m] || 0),
            backgroundColor: colors[idx].replace('0.7', '0.2'),
            borderColor: borderColors[idx],
            pointBackgroundColor: borderColors[idx],
            borderWidth: 2
        }}));

        new Chart(document.getElementById('radarChart'), {{
            type: 'radar',
            data: {{
                labels: categories.map(c => c.split(' ')[0]), // Shorten labels
                datasets: radarDatasets
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{ min: 0, max: 100, ticks: {{ stepSize: 20, display: false }} }}
                }}
            }}
        }});

        const timeRadarDatasets = models.map((m, idx) => ({{
            label: m,
            data: categories.map(cat => categoryTimeStats[cat][m] || 0),
            backgroundColor: colors[idx].replace('0.7', '0.2'),
            borderColor: borderColors[idx],
            pointBackgroundColor: borderColors[idx],
            borderWidth: 2
        }}));

        new Chart(document.getElementById('timeRadarChart'), {{
            type: 'radar',
            data: {{
                labels: categories.map(c => c.split(' ')[0]), 
                datasets: timeRadarDatasets
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{ r: {{ beginAtZero: true, ticks: {{ display: false }} }} }}
            }}
        }});

        // --- 3. RENDER PIE CHARTS (Errors) ---
        models.forEach((m, idx) => {{
            let success = 0, failJson = 0, failLogic = 0;
            results.forEach(r => {{
                const s = r[m] || "";
                if (s.includes("✅")) success++;
                else if (s.includes("FAIL")) failJson++;
                else if (s.includes("BAD LOGIC")) failLogic++;
            }});

            new Chart(document.getElementById('pieChart' + idx), {{
                type: 'doughnut',
                data: {{
                    labels: ['Success', 'JSON Error', 'Logic Error'],
                    datasets: [{{
                        data: [success, failJson, failLogic],
                        backgroundColor: ['#22c55e', '#ef4444', '#f59e0b']
                    }}]
                }},
                options: {{
                    plugins: {{ title: {{ display: true, text: m.toUpperCase() }} }}
                }}
            }});
        }});

        // --- 4. RENDER BAR CHART ---
        const overallSuccess = models.map(m => {{
            let total = 0;
            results.forEach(r => {{ if ((r[m] || "").includes("✅")) total++; }});
            return (total / results.length) * 100;
        }});

        new Chart(document.getElementById('barChart'), {{
            type: 'bar',
            data: {{
                labels: models,
                datasets: [{{
                    label: 'Overall Success Rate (%)',
                    data: overallSuccess,
                    backgroundColor: colors.slice(0, models.length),
                    borderColor: borderColors.slice(0, models.length),
                    borderWidth: 1
                }}]
            }},
            options: {{ scales: {{ y: {{ beginAtZero: true, max: 100 }} }} }}
        }});

        // --- 5. RENDER CATEGORY SUMMARY TABLE ---
        const catHeaderRow = document.getElementById('cat-table-header');
        models.forEach(m => {{
            const th = document.createElement('th');
            th.className = "px-6 py-3";
            th.innerText = m.toUpperCase();
            catHeaderRow.appendChild(th);
        }});

        const catTbody = document.getElementById('cat-table-body');
        categories.forEach(cat => {{
            const tr = document.createElement('tr');
            tr.className = "bg-white border-b hover:bg-gray-50";

            const tdCat = document.createElement('td');
            tdCat.className = "px-6 py-4 font-medium text-gray-900";
            tdCat.innerText = cat;
            tr.appendChild(tdCat);

            let maxScore = -1;
            models.forEach(m => {{
                const s = categoryStats[cat][m] || 0;
                if (s > maxScore) maxScore = s;
            }});

            models.forEach(m => {{
                const td = document.createElement('td');
                td.className = "px-6 py-4";

                const succ = Math.round(categoryStats[cat][m] || 0);
                const time = (categoryTimeStats[cat][m] || 0).toFixed(2);

                let colorClass = "text-gray-500";
                let badge = "";
                let cellClass = "";

                if (succ === maxScore && maxScore > 0) {{
                    colorClass = "text-green-700 font-bold";
                    badge = " 🏆";
                    cellClass = "bg-green-50";
                }} else if (succ >= 80) {{
                    colorClass = "text-green-600";
                }} else if (succ >= 50) {{
                    colorClass = "text-amber-600";
                }} else {{
                    colorClass = "text-red-600";
                }}

                if (cellClass) td.className += " " + cellClass;

                td.innerHTML = `<span class="${{colorClass}}">${{succ}}%${{badge}}</span> <span class="text-xs text-gray-400 ml-2">(${{time}}s)</span>`;
                tr.appendChild(td);
            }});
            catTbody.appendChild(tr);
        }});

        // --- 6. RENDER DETAILED TABLE ---
        const headerRow = document.getElementById('table-header');
        models.forEach(m => {{
            const th = document.createElement('th');
            th.className = "px-6 py-3";
            th.innerText = m.toUpperCase();
            headerRow.appendChild(th);
        }});

        const tbody = document.getElementById('table-body');

        function renderTable(data) {{
            tbody.innerHTML = '';
            data.sort((a,b) => (a.Category || "").localeCompare(b.Category || ""));
            let lastCategory = null;

            data.forEach(row => {{
                if (row.Category !== lastCategory) {{
                    const headerTr = document.createElement('tr');
                    headerTr.className = "bg-gray-100 border-b";
                    const th = document.createElement('th');
                    th.colSpan = models.length + 1;
                    th.className = "px-6 py-2 text-left text-xs font-bold text-gray-600 uppercase tracking-wider";
                    th.innerText = row.Category;
                    headerTr.appendChild(th);
                    tbody.appendChild(headerTr);
                    lastCategory = row.Category;
                }}

                const tr = document.createElement('tr');
                tr.className = "bg-white border-b hover:bg-gray-50";

                const tdPrompt = document.createElement('td');
                tdPrompt.className = "px-6 py-4";
                tdPrompt.innerHTML = `<div class="font-medium text-gray-900">${{row.Prompt}}</div>`;
                tr.appendChild(tdPrompt);

                models.forEach(m => {{
                    const td = document.createElement('td');
                    td.className = "px-6 py-4 align-top";

                    const rawStatus = row[m] || "N/A";
                    let rawJson = row[m + "_json"] || "{{}}";

                    let colorClass = "text-gray-400";
                    if (rawStatus.includes("✅")) colorClass = "text-green-600 font-bold";
                    if (rawStatus.includes("❌")) colorClass = "text-red-600 font-bold";
                    if (rawStatus.includes("⚠️")) colorClass = "text-amber-600 font-bold";

                    const container = document.createElement('div');

                    const statusDiv = document.createElement('div');
                    statusDiv.className = colorClass + " text-xs mb-2";
                    statusDiv.innerHTML = rawStatus.replace(/\\n/g, " &nbsp; ");
                    container.appendChild(statusDiv);

                    const details = document.createElement('details');
                    details.className = "group";
                    const summary = document.createElement('summary');
                    summary.className = "text-[10px] text-gray-400 cursor-pointer hover:text-indigo-600 flex items-center gap-1";
                    summary.innerHTML = `<span>JSON</span>`;
                    const pre = document.createElement('pre');
                    pre.className = "mt-2 p-2 bg-slate-800 text-green-400 rounded text-[10px] overflow-auto max-w-[200px]";
                    pre.textContent = rawJson;

                    details.appendChild(summary);
                    details.appendChild(pre);
                    container.appendChild(details);

                    td.appendChild(container);
                    tr.appendChild(td);
                }});
                tbody.appendChild(tr);
            }});
        }}
        renderTable(results);

        document.getElementById('searchInput').addEventListener('keyup', (e) => {{
            const term = e.target.value.toLowerCase();
            const filtered = results.filter(r => 
                r.Prompt.toLowerCase().includes(term) || 
                r.Category.toLowerCase().includes(term)
            );
            renderTable(filtered);
        }});

    </script>
</body>
</html>
    """

    with open("benchmark_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ HTML Report saved to: {sys.path[0]}/benchmark_report.html")


if __name__ == "__main__":
    choice = input("Run new benchmark? (y/n): ").lower().strip()

    data = []
    if choice == 'y':
        data = run_new_benchmark()
        if data:
            print(f"\nExporting to {CSV_FILENAME}...")
            with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
    else:
        data = load_existing_csv()

    if data:
        generate_html_report(data)
    else:
        print("No data available.")