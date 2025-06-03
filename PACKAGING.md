# SpinQLabLink 打包说明

本文档提供了如何构建、安装和分发 SpinQLabLink 包的详细说明。

## 前提条件

确保已安装以下工具：

```bash
pip install wheel setuptools build twine
```

## 构建方法

### 方法1：使用打包脚本（推荐）

我们提供了一个打包脚本，可以自动化构建过程：

```bash
python build_package.py
```

这将在 `dist/` 目录中生成 `.whl` 和 `.tar.gz` 格式的分发包。

### 方法2：手动构建

如果您想手动构建，可以按照以下步骤操作：

1. 清理旧的构建文件（可选）：
   ```bash
   rm -rf build/ dist/ *.egg-info/
   ```

2. 构建分发包：
   ```bash
   python -m build
   ```

## 安装方法

### 从本地安装

构建完成后，您可以使用以下命令安装生成的 `.whl` 文件：

```bash
pip install dist/spinqlablink-0.1.0-py3-none-any.whl
```

### 开发模式安装

如果您需要在开发过程中测试包，可以使用开发模式安装：

```bash
pip install -e .
```

这样，您对代码的修改会立即反映在安装的包中，无需重新安装。

## 分发到 PyPI

如果您想将包发布到 PyPI，可以使用以下命令：

```bash
# 上传到测试 PyPI（推荐先测试）
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# 上传到正式 PyPI
twine upload dist/*
```

注意：上传到 PyPI 需要有 PyPI 账号，并且需要配置 `~/.pypirc` 文件或在命令行中提供用户名和密码。

## 验证安装

安装后，您可以通过以下方式验证安装是否成功：

```bash
# 验证命令行工具
spinqlablink --help

# 验证导入
python -c "import spinqlablink; print(spinqlablink.__version__)"
```

## 故障排除

如果在构建或安装过程中遇到问题，请检查：

1. 是否已安装所有必需的依赖项
2. 包结构是否正确
3. `setup.py` 是否配置正确

如果问题仍然存在，请提交 GitHub Issue 或联系维护者。 