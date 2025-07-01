import pytest
from salary_calculator.calculator import InternSalaryCalculator


def test_valid_calculation():
    calc = InternSalaryCalculator({'A': 20})
    assert calc.calculate_hourly_wage('A', 10) == 200
    assert calc.calculate_total_salary('A', 10, [(5, 10)]) == 250


def test_invalid_level():
    calc = InternSalaryCalculator()
    with pytest.raises(ValueError):
        calc.get_hourly_rate('X')
    with pytest.raises(ValueError):
        calc.calculate_hourly_wage('X', 10)


def test_negative_hours():
    calc = InternSalaryCalculator()
    with pytest.raises(ValueError):
        calc.calculate_hourly_wage('A', -5)


def test_piecework_wage():
    calc = InternSalaryCalculator()
    assert calc.calculate_piecework_wage([(10, 5)]) == 50
    assert calc.calculate_piecework_wage([(5, 10), (3, 20)]) == 110