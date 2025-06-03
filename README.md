# 专利匹配标注管理

## 安装

```
pip install pdm
```

## 配置

### Python依赖

```
pdm install
```

### 数据文件

项目根目录创建`data`文件夹，在文件夹里放`匹配失败起草单位v4_无专利数据.csv`。


## 运行

### 分配数据

```
pdm run split
```

或者

```
pdm run python -m patent_checker.splitter
```

### 检查数据

```
pdm run check
```

或者

```
pdm run python -m patent_checker.checker
```

### 检查单个数据

```
pdm run single-check
```

或者

```
pdm run python -m patent_checker.single_checker
```
