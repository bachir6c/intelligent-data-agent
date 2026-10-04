import json
from pathlib import Path

from agent import run_agent


PROJECT_ROOT = Path(__file__).resolve().parent.parent

QUESTIONS_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "questions.json"
)

RESULTS_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "results.json"
)
def normalize_text(text):
    return (
        text.lower()
        .replace("\u202f", " ")
        .replace("\xa0", " ")
        .replace("_", " ")
        .replace("agency", "agence")
    )
def check_answer(question_data, answer, tools_used):
    """
    Vérifie automatiquement ce qu'on peut vérifier simplement.
    """

    checks = {}

    # ---------------------------------
    # Vérification utilisation d'outils
    # ---------------------------------

    if "expected_tool_use" in question_data:

        expected = question_data["expected_tool_use"]
        actual = len(tools_used) > 0

        checks["tool_use_correct"] = (
            expected == actual
        )
    if "expected_tools" in question_data:

        expected_tools = question_data["expected_tools"]

        checks["tool_selection_correct"] = all(
            tool in tools_used
            for tool in expected_tools
        )
    # ---------------------------------
    # Réponse exacte / valeur attendue
    # ---------------------------------

    if "expected_answer" in question_data:

        expected = normalize_text(
            str(question_data["expected_answer"])
        ).replace(" ", "")

        normalized_answer = normalize_text(
            answer
        ).replace(" ", "")

        checks["answer_correct"] = (
            expected in normalized_answer
        )

    # ---------------------------------
    # Éléments qui doivent apparaître
    # ---------------------------------

    if "expected_contains" in question_data:

        expected_values = question_data[
            "expected_contains"
        ]

        normalized_answer = normalize_text(answer).replace(" ", "")

        checks["expected_content_found"] = all(
            normalize_text(str(value)).replace(" ", "") in normalized_answer
            for value in expected_values
        )

    # ---------------------------------
    # Graphique
    # ---------------------------------

    if question_data.get("expected_chart"):

        checks["chart_created"] = (
            "plot_daily_activity" in tools_used
        )

    # ---------------------------------
    # Question impossible
    # ---------------------------------

    if question_data.get(
        "expected_behavior"
    ) == "abstain":

        abstention_phrases = [
            "ne contient pas",
            "pas disponible",
            "impossible",
            "ne peux pas",
            "aucune donnée",
            "données disponibles",
            "pas d'information"
        ]

        checks["abstention_correct"] = any(
            phrase in answer.lower()
            for phrase in abstention_phrases
        )

    return checks


def run_benchmark():

    with open(
        QUESTIONS_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        questions = json.load(file)

    # Charger les anciens résultats s'ils existent
    if RESULTS_PATH.exists():
        with open(
            RESULTS_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            old_data = json.load(file)

        results_by_id = {
            result["id"]: result
            for result in old_data.get("results", [])
        }

    else:
        results_by_id = {}

    for question_data in questions:

        question_id = question_data["id"]

        # Si la question a déjà réussi, on ne la relance pas
        previous_result = results_by_id.get(question_id)

        if (
            previous_result
            and previous_result.get("passed") is True
        ):
            print(
                f"\nQuestion {question_id}: "
                f"SKIP (déjà réussie)"
            )
            continue

        print(
            f"\nQuestion {question_id}: "
            f"{question_data['question']}"
        )

        try:
            result = run_agent(
                question_data["question"],
                return_trace=True,
                verbose=False
            )

        except Exception as error:

            print(f"ERROR: {error}")

            results_by_id[question_id] = {
                "id": question_id,
                "category": question_data["category"],
                "question": question_data["question"],
                "answer": "",
                "tools_used": [],
                "checks": {},
                "passed": False,
                "error": str(error)
            }

            if "429" in str(error):
                print(
                    "\nRate limit Groq atteint. "
                    "Arrêt du benchmark."
                )
                break

            continue


        answer = result.get("answer") or ""
        tools_used = result.get("tools", [])

        checks = check_answer(
            question_data,
            answer,
            tools_used
        )

        question_passed = (
            all(checks.values())
            if checks
            else True
        )

        status = (
            "PASS"
            if question_passed
            else "FAIL"
        )

        print(f"Status: {status}")
        print(f"Tools: {tools_used}")
        print(f"Checks: {checks}")
        print("Answer:")
        print(answer)

        # Remplace l'ancien résultat de cette question
        results_by_id[question_id] = {
            "id": question_id,
            "category": question_data["category"],
            "question": question_data["question"],
            "answer": answer,
            "tools_used": tools_used,
            "checks": checks,
            "passed": question_passed
        }

    # Remettre les résultats dans l'ordre des questions
    results = [
        results_by_id[q["id"]]
        for q in questions
        if q["id"] in results_by_id
    ]

    # On ne compte pas les erreurs API comme des questions évaluées
    evaluated_results = [
        result
        for result in results
        if "error" not in result
    ]

    tool_selection_checks = [
        result["checks"]["tool_selection_correct"]
        for result in evaluated_results
        if "tool_selection_correct" in result.get("checks", {})
    ]
    total_evaluated = len(evaluated_results)

    passed = sum(
        result["passed"]
        for result in evaluated_results
    )
    failed = total_evaluated - passed

    tool_checks = [
        result["checks"]["tool_use_correct"]
        for result in evaluated_results
        if "tool_use_correct" in result.get("checks", {})
    ]

    tool_selection_checks = [
        result["checks"]["tool_selection_correct"]
        for result in evaluated_results
        if "tool_selection_correct" in result.get("checks", {})
    ]

    content_checks = [
        result["checks"]["expected_content_found"]
        for result in evaluated_results
        if "expected_content_found" in result.get("checks", {})
    ]

    answer_checks = [
        result["checks"]["answer_correct"]
        for result in evaluated_results
        if "answer_correct" in result.get("checks", {})
    ]

    abstention_checks = [
        result["checks"]["abstention_correct"]
        for result in evaluated_results
        if "abstention_correct" in result.get("checks", {})
    ]

    chart_checks = [
        result["checks"]["chart_created"]
        for result in evaluated_results
        if "chart_created" in result.get("checks", {})
    ]

    def percentage(values):
        if not values:
            return None

        return round(
            sum(values) / len(values) * 100,
            2
        )

    remaining = (
        len(questions)
        - total_evaluated
    )

    accuracy = (
        passed / total_evaluated * 100
        if total_evaluated > 0
        else 0
    )

    summary = {
        "total_questions": len(questions),
        "evaluated": total_evaluated,
        "passed": passed,
        "failed": failed,
        "remaining": remaining,
        "accuracy_percent": round(accuracy, 2),
        "results": results,
        "metrics": {
            "tool_use_accuracy": percentage(tool_checks),
            "tool_selection_accuracy": percentage(tool_selection_checks),
            "content_accuracy": percentage(content_checks),
            "answer_accuracy": percentage(answer_checks),
            "abstention_accuracy": percentage(abstention_checks),
            "chart_success_rate": percentage(chart_checks)
        }
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            summary,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n==============================")
    print("BENCHMARK COMPLETE")
    print("==============================")
    print(f"Questions totales: {len(questions)}")
    print(f"Évaluées: {total_evaluated}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Restantes: {remaining}")
    print(f"Accuracy: {accuracy:.2f}%")

    print("\nMetrics:")
    print(f"Tool use: {percentage(tool_checks)}%")
    print(f"Tool selection: {percentage(tool_selection_checks)}%")
    print(f"Content: {percentage(content_checks)}%")
    print(f"Answer: {percentage(answer_checks)}%")
    print(f"Abstention: {percentage(abstention_checks)}%")
    print(f"Chart: {percentage(chart_checks)}%")

    print(
        f"\nResults saved to: "
        f"{RESULTS_PATH}"
    )
if __name__ == "__main__":
    run_benchmark()