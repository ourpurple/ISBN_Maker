# ISBN Barcode Generator

批量ISBN条码生成器 - 生成符合GS1标准的TIF格式条码图片

## 功能特性

- ISBN-13格式验证和解析
- EAN-13条码编码
- 2位/5位附加码支持
- 多种颜色模式（黑白、灰度、RGB、CMYK）
- 自定义文字样式和位置
- 模板管理
- 批量处理
- 现代化PyQt6图形界面
- 独立Windows可执行文件打包

## 安装

### 开发环境

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 运行

```bash
python -m isbn_barcode_generator.main
```

## 测试

```bash
pytest
```

## 打包

```bash
pyinstaller isbn_barcode_generator.spec
```

## 项目结构

```
isbn-barcode-generator/
├── src/
│   └── isbn_barcode_generator/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── validator.py      # ISBN验证器
│       │   ├── encoder.py        # EAN-13编码器
│       │   ├── addon_encoder.py  # 附加码编码器
│       │   ├── renderer.py       # TIF渲染器
│       │   ├── template_manager.py  # 模板管理器
│       │   └── batch_processor.py   # 批量处理器
│       └── gui/
│           ├── __init__.py
│           └── main_window.py    # 主窗口
├── tests/
│   ├── __init__.py
│   ├── test_validator.py
│   ├── test_encoder.py
│   ├── test_addon_encoder.py
│   ├── test_renderer.py
│   ├── test_template_manager.py
│   └── test_batch_processor.py
├── pyproject.toml
└── README.md
```

## 许可证

MIT License
