class InternSalaryCalculator:
    def __init__(self, hourly_rates=None):
        """初始化实习生薪资计算器"""
        self.hourly_rates = hourly_rates or {'A': 20, 'B': 25, 'C': 30}

    def get_hourly_rate(self, level):
        """获取实习生职级对应的时薪"""
        rate = self.hourly_rates.get(level)
        if rate is None:
            raise ValueError(f"错误：未知职级 '{level}'，请检查配置")
        return rate

    def validate_positive(self, value, name):
        """校验参数是否为非负数"""
        if value < 0:
            raise ValueError(f"{name} 不能为负数，当前值：{value}")

    def calculate_hourly_wage(self, level, hours):
        """计算实习生计时工资"""
        self.validate_positive(hours, "工时")
        rate = self.get_hourly_rate(level)
        return rate * hours

    def calculate_piecework_wage(self, piece_items):
        """计算实习生计件工资"""
        total_piece = 0
        for quantity, rate in piece_items:
            self.validate_positive(quantity, "计件数量")
            self.validate_positive(rate, "计件单价")
            total_piece += quantity * rate
        return total_piece

    def calculate_total_salary(self, level, hours, piece_items):
        """计算实习生总薪资"""
        hourly_wage = self.calculate_hourly_wage(level, hours)
        piece_wage = self.calculate_piecework_wage(piece_items)
        return hourly_wage + piece_wage
    def calculate_performance_wage(self):
        """绩效工资（暂不考虑，默认为0）"""
        return 0

    def print_salary_details(self, name, level, hours, piece_items):
        """打印薪资计算明细"""
        hourly_wage = self.calculate_hourly_wage(level, hours)
        piece_wage = self.calculate_piecework_wage(piece_items)
        total_salary = hourly_wage + piece_wage

        print(f"\n===== {name} 的薪资计算明细 =====")
        print(f"职级：{level}")
        print(f"时薪：{self.get_hourly_rate(level)} 元/小时")
        print(f"工时：{hours} 小时")
        print(f"计时工资：{hourly_wage} 元")

        print("\n计件任务：")
        for i, (quantity, rate) in enumerate(piece_items, start=1):
            subtotal = quantity * rate
            print(f"  任务{i}: {quantity}件 × {rate}元/件 = {subtotal}元")
        print(f"计件工资合计：{piece_wage} 元")

        print(f"\n总薪资（不包含绩效工资）：{total_salary} 元")


# 示例用法
'''if __name__ == "__main__":
    # 初始化计算器
    calculator = InternSalaryCalculator({'A': 22, 'B': 28, 'C': 35})

    # 定义实习生信息
    intern_name = "张三"
    intern_level = "B"  # 确定的职级
    work_hours = 40  # 总工时

    # 完成的计件任务
    piece_tasks = [
        (50, 3),  # 50件，单价3元
        (30, 5)  # 30件，单价5元
    ]

    # 计算并打印薪资
    calculator.print_salary_details(intern_name, intern_level, work_hours, piece_tasks)'''