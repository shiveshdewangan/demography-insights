import json
import re
import os
import time
from aayush2 import create_demografy_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize Judge 
# Use the same working model for the judge
judge_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

def run_automated_eval():
    agent = create_demografy_agent()
    with open('golden_dataset.json', 'r') as f:
        dataset = json.load(f)
    
    results = []
    for entry in dataset:
        print(f"Running Eval for ID {entry['id']}...")
        
        start_time = time.time()
        try:
            # EDGE CASE: Timeout handling (simulated via max_iterations in agent)
            response = agent.invoke({"input": entry['question']})
            actual_output = response.get("output", "Empty Response")
            
            # EDGE CASE: Empty Result Detection
            if "I don't know" in actual_output or "no data" in actual_output.lower():
                 actual_output = "No results found in database."
                 
        except Exception as e:
            # EDGE CASE: Malformed Query / Execution Error
            actual_output = f"Execution Error: {str(e)}"
        
        latency = time.time() - start_time
        
        # Scoring Logic
        score_data = score_with_judge(entry, actual_output)
        
        results.append({
            "id": entry['id'],
            "question": entry['question'],
            "output": actual_output,
            "latency": f"{latency:.2f}s",
            "score": score_data['score'],
            "reason": score_data['reason']
        })

    with open('eval_report.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("✅ Evaluation complete. Check eval_report.json")

def score_with_judge(entry, actual_output):
    prompt = f"""
    You are a Senior Data Auditor for Demografy, an AUSTRALIAN demographic platform.
    Evaluate the Agent's performance based on the following context.

    ### PROJECT CONTEXT:
    - This is AUSTRALIAN demographic data (SA2/Suburbs).
    - Valid States: Victoria, New South Wales, Queensland, Western Australia, South Australia, Tasmania, Northern Territory, Australian Capital Territory.
    - KPIs: kpi_1 (Prosperity), kpi_2 (Diversity), kpi_3 (Migration), kpi_4 (Learning), kpi_5 (Social Housing), kpi_6 (Equity), kpi_7 (Rental), kpi_8 (Anchor), kpi_9 (Mobility), kpi_10 (Young Family).

    ### EVALUATION DATA:
    - User Question: {entry['question']}
    - Ground Truth Pattern: {entry['expected_sql_pattern']}
    - Agent's Output: {actual_output}

    ### SCORING RUBRIC (1-5):
    - 5 (Perfect): Correct KPI column used, states mapped to full names, logic is flawless.
    - 4 (Good): Correct data/logic, but minor formatting or wording differences.
    - 3 (Average): Mostly correct logic, but small errors (e.g., wrong limit or slightly off filter value).
    - 2 (Poor): Significant errors, wrong KPI column, or failed to handle the state correctly.
    - 1 (Fail): Hallucinated data, SQL syntax error, or completely wrong answer.

    ### INSTRUCTIONS:
    - Do NOT penalize "Australian Capital Territory"; it is a valid territory.
    - Look at the Ground Truth Pattern to verify the KPI column used.
    
    Return JSON only: {{"score": int, "reason": str}}
    """

    raw = judge_llm.invoke(prompt).content
    # Clean markdown and parse
    clean = re.sub(r'```json\s*|```', '', raw).strip()
    return json.loads(clean)

if __name__ == "__main__":
    run_automated_eval()
