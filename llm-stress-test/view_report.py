import csv
import os
import webbrowser
import json

INPUT_FILE = "results30.csv"
OUTPUT_FILE = "report.html"


def get_color(score_str):
    """Returns a color based on the similarity score."""
    try:
        score = float(score_str.replace("%", ""))
        if score >= 90: return "#d4edda", "#155724"  # Green
        if score >= 70: return "#fff3cd", "#856404"  # Yellow/Orange
        return "#f8d7da", "#721c24"  # Red
    except:
        return "#ffffff", "#000000"


def format_json(json_str):
    """Pretty prints JSON string for better readability."""
    try:
        # It might be double encoded, so we try to load it
        parsed = json.loads(json_str)
        return json.dumps(parsed, indent=2)
    except:
        return json_str


# We use simple placeholders like {{ROWS}} to avoid conflict with CSS { }
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Stress Test Report</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; padding: 20px; }
        h1 { text-align: center; color: #333; }
        .summary { text-align: center; margin-bottom: 20px; font-size: 1.2em; }
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; vertical-align: top; }
        th { background-color: #007bff; color: white; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.1em; }
        tr:hover { background-color: #f1f1f1; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; border: 1px solid #eee; white-space: pre-wrap; word-wrap: break-word; font-size: 0.9em; margin: 0; }
        .badge { padding: 5px 10px; border-radius: 12px; font-weight: bold; display: inline-block; min-width: 60px; text-align: center; }
        .mistake-type { font-style: italic; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>LLM Stress Test Results</h1>
    <div class="summary" id="summary">Loading stats...</div>
    <table>
        <thead>
            <tr>
                <th width="5%">ID</th>
                <th width="20%">Prompt & Mistake Type</th>
                <th width="30%">LLM Output</th>
                <th width="30%">Expected Plan</th>
                <th width="15%">Similarity</th>
            </tr>
        </thead>
        <tbody>
            {{ROWS}}
        </tbody>
    </table>
    <script>
        document.getElementById('summary').innerText = "Total Tests: {{TOTAL}} | Average Score: {{SCORE}}%";
    </script>
</body>
</html>
"""


def generate_report():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run main.py first.")
        return

    table_rows = ""
    total_score = 0
    count = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            score_str = row["Similarity %"]
            try:
                total_score += float(score_str.replace("%", ""))
            except:
                pass

            bg_color, text_color = get_color(score_str)

            # Escape HTML characters to prevent breakage if LLM outputs <>
            safe_llm = format_json(row['LLM Output']).replace("<", "&lt;").replace(">", "&gt;")
            safe_expected = format_json(row['Expected Output']).replace("<", "&lt;").replace(">", "&gt;")

            row_html = f"""
            <tr>
                <td><strong>{row['ID']}</strong></td>
                <td>
                    <div><strong>{row['User Prompt']}</strong></div>
                    <div class="mistake-type">{row['Mistake Type']}</div>
                </td>
                <td><pre>{safe_llm}</pre></td>
                <td><pre>{safe_expected}</pre></td>
                <td>
                    <span class="badge" style="background-color: {bg_color}; color: {text_color}">
                        {score_str}
                    </span>
                </td>
            </tr>
            """
            table_rows += row_html

    avg_score = f"{total_score / count:.2f}" if count > 0 else "0"

    # We use .replace() here, which ignores the CSS curly braces
    final_html = html_template.replace("{{ROWS}}", table_rows)
    final_html = final_html.replace("{{TOTAL}}", str(count))
    final_html = final_html.replace("{{SCORE}}", avg_score)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Report generated: {OUTPUT_FILE}")
    print("Opening in browser...")
    webbrowser.open('file://' + os.path.realpath(OUTPUT_FILE))


if __name__ == "__main__":
    generate_report()