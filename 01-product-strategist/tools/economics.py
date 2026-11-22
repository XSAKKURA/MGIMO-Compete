"""Когортный расчёт учебного оператора. Только стандартная библиотека Python 3."""
import argparse
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def calculate(data, scenario):
    """Посчитать экспозицию до декабря и инкремент к обычному обслуживанию."""
    margin = Decimal(str(data["margin_per_month"]))
    delta = Decimal(str(scenario["paid_probability_difference"]))
    cohorts = scenario["cohorts"]
    costs = scenario.get("quarterly_direct_cost")
    annual = scenario.get("annual_direct_cost")
    if not margin.is_finite() or margin <= 0 or not delta.is_finite() or abs(delta) > 1:
        raise ValueError("Проверьте ставку и абсолютную разницу вероятностей")
    if any(type(m) is not int or not 1 <= m <= 12 or type(n) is not int or n < 0
           for m, n in cohorts):
        raise ValueError("Когорта требует целого месяца 1–12 и числа уникальных номеров ≥ 0")
    if costs is None and annual is None:
        raise ValueError("Укажите прямые расходы за год или за четыре квартала")
    if costs is not None:
        costs = [Decimal(str(c)) for c in costs]
        if len(costs) != 4 or any(not c.is_finite() or c < 0 for c in costs):
            raise ValueError("Требуются четыре неотрицательных квартальных расхода")
        if annual is not None and sum(costs) != Decimal(str(annual)):
            raise ValueError("Годовая смета расходится с квартальной. Уточните версию")
        annual = sum(costs)
    annual = Decimal(str(annual))
    if not annual.is_finite() or annual < 0:
        raise ValueError("Годовые расходы должны быть конечными и неотрицательными")
    exposure = [sum(n for start, n in cohorts if start <= m) for m in range(1, 13)]
    paid = [sum(exposure[q:q+3]) * delta for q in range(0, 12, 3)]
    contribution = sum(paid) * margin - annual
    profit = data["base_profit"] + contribution
    required = max(Decimal(0), (data["target_profit"] - data["base_profit"] + annual) / margin)
    quarterly = None if costs is None else [p * margin - c for p, c in zip(paid, costs)]
    return dict(exposure=sum(exposure), paid_months=sum(paid), direct_cost=annual,
                contribution=contribution, quarterly=quarterly, profit=profit,
                gap_to_target=data["target_profit"] - profit, required_paid_months=required,
                required_delta=required / sum(exposure) if sum(exposure) else None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=ROOT / "demo/inputs.json")
    args = parser.parse_args()
    try:
        inputs = json.loads(args.input.read_text(encoding="utf-8"), parse_float=Decimal)
        results = {name: calculate(inputs, scenario) for name, scenario in inputs["scenarios"].items()}
    except (ValueError, OSError, KeyError, TypeError, ArithmeticError) as error:
        parser.exit(2, f"Ошибка исходных данных: {error}\n")
    print(json.dumps(results, default=str, ensure_ascii=False, indent=2))
