# E:\PythonProject1\salary_calculator\__main__.py
import typer
from .calculator import InternSalaryCalculator

app = typer.Typer()
calc = InternSalaryCalculator()


@app.command()
def calculate(
        name: str = typer.Argument(..., help="实习生姓名"),
        level: str = typer.Argument(..., help="职级(A/B/C)"),
        hours: float = typer.Argument(..., help="工时(小时)"),
        pieces: str = typer.Option("", "--pieces", "-p",
                                   help="计件任务，格式：数量1,单价1;数量2,单价2")
):
    # 解析计件任务
    piece_items = []
    if pieces:
        for task in pieces.split(";"):
            if task:
                qty, rate = task.split(",")
                piece_items.append((float(qty), float(rate)))

    # 计算并显示结果
    hourly_wage = calc.calculate_hourly_wage(level, hours)
    piece_wage = calc.calculate_piecework_wage(piece_items)
    total = hourly_wage + piece_wage

    typer.echo(f"\n===== {name} 的薪资计算 =====")
    typer.echo(f"职级: {level}")
    typer.echo(f"时薪: {calc.get_hourly_rate(level)} 元/小时")
    typer.echo(f"工时: {hours} 小时")
    typer.echo(f"计时工资: {hourly_wage} 元")

    typer.echo("\n计件任务明细:")
    for i, (qty, rate) in enumerate(piece_items, 1):
        typer.echo(f"  任务{i}: {qty}件 × {rate}元 = {qty * rate}元")

    typer.echo(f"\n计件工资: {piece_wage} 元")
    typer.echo(f"总薪资: {total} 元")
    typer.echo("-" * 40)


if __name__ == "__main__":
    app()