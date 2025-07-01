# E:\PythonProject1\conftest.py
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path
root_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(root_dir))