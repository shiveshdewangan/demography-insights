"""
Offline evaluation: runs test questions through the agent, judges each response, prints a report.
Usage: python -m eval.run_eval
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.prompts import ask_question
from eval.judge import judge_response

TEST_CASES = [
    "What are the top 5 most prosperous suburbs in New South Wales?",
    "Which state has the highest average diversity index?",
    "List the top 10 most affordable rental suburbs in Queensland.",
    "What are the suburbs in Victoria with social housing above 20%?",
    "Which suburb has the highest young family presence in Western Australia?",
    "Compare average home ownership vs rental access across all states.",
    "What is the average education level in the Australian Capital Territory?",
    "Top 5 most stable (resident anchor) suburbs in South Australia.",
    "Which suburbs in Tasmania have a migration footprint above 50%?",
    "What are the top 3 suburbs with the lowest household mobility in Victoria?",
]

SCORE_LABELS = {5: "PERFECT", 4: "GOOD", 3: "OK", 2: "POOR", 1: "FAIL", 0: "ERROR"}


def run_eval():
    results = []

    print("=" * 70)
    print("DEMOGRAFY AGENT EVALUATION")
    print("=" * 70)

    for i, question in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] {question}")
        print("-" * 60)

        answer = ask_question(question)
        print(f"Answer: {answer[:300]}{'...' if len(answer) > 300 else ''}")

        verdict = judge_response(question, answer)
        score = verdict.get("score", 0)
        label = SCORE_LABELS.get(score, "UNKNOWN")

        print(f"Score:        {score}/5  ({label})")
        print(f"Relevance:    {verdict.get('relevance', '-')}")
        print(f"Groundedness: {verdict.get('groundedness', '-')}")
        print(f"Completeness: {verdict.get('completeness', '-')}")
        print(f"Reasoning:    {verdict.get('reasoning', '-')}")

        results.append({"question": question, "answer": answer, "verdict": verdict})

    # Summary
    scores = [r["verdict"].get("score", 0) for r in results]
    valid_scores = [s for s in scores if s > 0]
    avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Questions evaluated : {len(results)}")
    print(f"Average score       : {avg:.2f} / 5")
    print(f"Score distribution  :")
    for label_score in [5, 4, 3, 2, 1, 0]:
        count = scores.count(label_score)
        if count:
            bar = "█" * count
            print(f"  {label_score} ({SCORE_LABELS[label_score]:<7}): {bar} {count}")

    failed = [r for r in results if r["verdict"].get("score", 0) <= 2]
    if failed:
        print(f"\nLow-scoring questions (score ≤ 2):")
        for r in failed:
            print(f"  [{r['verdict'].get('score')}] {r['question']}")

    return results


if __name__ == "__main__":
    run_eval()