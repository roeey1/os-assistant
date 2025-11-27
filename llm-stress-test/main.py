import ollama
import json
import csv
import difflib
from pathlib import Path

# CONFIGURATION
MODEL_NAME = "llama3"
INPUT_FILE = "test_cases.json"
OUTPUT_FILE = "results30.csv"

# --- 1. STRICT SYSTEM PROMPT ---
# We added explicit "JSON Structure" instructions to stop the LLM from being creative with formats.
SYSTEM_PROMPT = """
You are an OS Assistant. translate user commands into a JSON tool call.
Output MUST be a single JSON object with exactly two keys: "tool" and "args".

Available Tools:
- create_file(path, content)
- move_file(source, destination)
- list_directory(path)
- create_folder(path)
- delete_file(path)
- get_disk_usage(path)
- copy_file(source, destination)
- rename_file(old_path, new_path)

MANDATORY JSON STRUCTURE:
{
  "tool": "tool_name_here",
  "args": {
    "arg_name": "value"
  }
}

Do not output lists, markdown, or explanations. Only the JSON object.
"""

# --- 2. SMART PATH NORMALIZER ---
def normalize_path(path_str):
    """
    Standardizes paths so '~/Documents/file.txt' matches 'documents/file.txt'.
    1. Lowercase
    2. Remove '~' and './'
    3. Convert backslashes to forward slashes
    """
    if not isinstance(path_str, str):
        return str(path_str)

    p = path_str.lower().strip()
    p = p.replace("\\", "/") # Windows fix
    p = p.replace("~/", "")  # Remove home alias
    p = p.replace("./", "")  # Remove current dir alias

    # Optional: Remove leading slash to make everything relative
    if p.startswith("/"):
        p = p[1:]

    return p

# --- 3. SEMANTIC COMPARISON LOGIC ---
def calculate_score(expected_json, actual_json):
    """
    Compares two JSON objects based on logic, not string matching.
    Returns a score from 0 to 100.
    """
    # 1. Check if Tool matches
    if expected_json.get("tool") != actual_json.get("tool"):
        return 0.0 # Wrong tool is an automatic fail

    expected_args = expected_json.get("args", {})
    actual_args = actual_json.get("args", {})

    total_args = len(expected_args)
    if total_args == 0:
        return 100.0 # No args expected, and tool matched

    matches = 0

    for key, expected_val in expected_args.items():
        actual_val = actual_args.get(key)

        # Normalize strings for comparison (paths, etc)
        norm_expected = normalize_path(expected_val)
        norm_actual = normalize_path(actual_val)

        # Exact match after normalization
        if norm_expected == norm_actual:
            matches += 1
        else:
            # Fallback: Fuzzy match for things like "content" that might vary slightly
            # If similarity is > 85% after normalization, we count it.
            seq = difflib.SequenceMatcher(None, norm_expected, norm_actual)
            if seq.ratio() > 0.85:
                matches += 1

    # Calculate percentage of correct arguments
    return (matches / total_args) * 100

def run_tests():
    # Load Test Cases
    try:
        with open(INPUT_FILE, "r") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}")
        return

    results = []

    print(f"Starting Stress Test on model: {MODEL_NAME}...\n")

    for case in test_cases:
        prompt = case["user_prompt"]
        print(f"Testing ID {case['id']}...")

        try:
            # Call Ollama
            response = ollama.chat(model=MODEL_NAME, messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ], format='json')

            llm_output_str = response['message']['content']

            # Parse LLM Output
            try:
                llm_output_json = json.loads(llm_output_str)

                # Handle edge case where LLM puts everything in a list [ { ... } ]
                if isinstance(llm_output_json, list) and len(llm_output_json) > 0:
                    llm_output_json = llm_output_json[0]

            except json.JSONDecodeError:
                llm_output_json = {"error": "Invalid JSON", "raw": llm_output_str}

            # Calculate Semantic Score
            if "error" in llm_output_json:
                score = 0
            else:
                score = calculate_score(case["expected_json"], llm_output_json)

            # Format outputs for CSV (Pretty Print)
            expected_str = json.dumps(case["expected_json"], indent=2)
            actual_str = json.dumps(llm_output_json, indent=2)

            results.append({
                "ID": case["id"],
                "Mistake Type": case["mistake_type"],
                "User Prompt": prompt,
                "LLM Output": actual_str,
                "Expected Output": expected_str,
                "Similarity %": f"{score:.2f}%"
            })

        except Exception as e:
            print(f"FAILED on ID {case['id']}: {e}")
            results.append({
                "ID": case["id"],
                "Mistake Type": "CRITICAL ERROR",
                "User Prompt": prompt,
                "LLM Output": str(e),
                "Expected Output": "",
                "Similarity %": "0.00%"
            })

    # Save to CSV
    keys = results[0].keys()
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)

    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_tests()