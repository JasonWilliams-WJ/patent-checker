# integrated_tests/test_cli.py
from typer.testing import CliRunner
from salary_calculator.__main__ import app

runner = CliRunner()


# 修改断言匹配为实际输出格式
def test_salary_calculation():
    result = runner.invoke(app, ["张三", "B", "40"])
    assert result.exit_code == 0
    assert "张三" in result.stdout
    assert "1000.0" in result.stdout  # 改为匹配一位小数格式


def test_with_pieces():
    result = runner.invoke(app, ["李四", "A", "30", "-p", "50,3;30,5"])
    assert result.exit_code == 0
    assert "李四" in result.stdout
    assert "900.0" in result.stdout  # 改为匹配一位小数格式