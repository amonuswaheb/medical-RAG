import csv
import subprocess
import json
import re

csv_files = [
    "eval/Day3_Refusal_Test_Cases.csv",
    "eval/Day4_Starter_Benchmark.csv"
]
output_md = "evaluation_report_day3_4.md"

def extract_json(output):
    match = re.search(r'Structured JSON Response:\s*(\{.*?\})\s*={10,}', output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None

def run_eval():
    results = []
    
    for csv_path in csv_files:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                question = row.get('Question') or row.get('Prompt')
                if not question:
                    continue
                # Try multiple column names since they might differ
                expected = row.get('Expected Source (Document / Section / Page)') or row.get('Expected Behavior') or 'Unknown'
                category = row.get('Category', 'N/A')
                
                print(f"Running question: {question}")
                process = subprocess.run(
                    ["ragv\\Scripts\\python", "pipeline.py", question],
                    capture_output=True, text=True
                )
                
                output = process.stdout
                json_resp = extract_json(output)
                
                if json_resp:
                    rec = json_resp.get('recommendation', '')
                    conf = json_resp.get('confidence', '')
                    cites = json_resp.get('citations', [])
                    cite_str = ", ".join([f"Page {c.get('page', '?')}" for c in cites])
                    if conf.lower() == 'insufficient':
                        cite_str = "Refused (Expected)"
                else:
                    rec = "Failed to parse"
                    conf = "N/A"
                    cite_str = "N/A"
                    
                results.append({
                    'file': csv_path.split('/')[-1],
                    'category': category,
                    'question': question,
                    'expected': expected,
                    'recommendation': rec,
                    'confidence': conf,
                    'citations': cite_str
                })

    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("# RAG Evaluation Report (Day 3 & Day 4)\n\n")
        
        current_file = ""
        for i, res in enumerate(results, 1):
            if current_file != res['file']:
                current_file = res['file']
                f.write(f"\n## File: {current_file}\n")
                
            f.write(f"### Q{i}: {res['question']}\n")
            f.write(f"- **Category**: {res['category']}\n")
            f.write(f"- **Expected Behavior/Source**: {res['expected']}\n")
            f.write(f"- **RAG Confidence**: {res['confidence'].upper()}\n")
            f.write(f"- **RAG Citations**: {res['citations']}\n")
            f.write(f"- **Recommendation**: {res['recommendation']}\n\n")

if __name__ == "__main__":
    run_eval()
