"""
Template Manager Tests - 模板管理器测试
"""

import os
import tempfile
import shutil
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.isbn_barcode_generator.core.template_manager import TemplateManager, Template


# 定义配置值的策略
color_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)

color_mode_strategy = st.sampled_from(["BITMAP", "GRAYSCALE", "RGB", "CMYK", "1", "L"])

text_alignment_strategy = st.sampled_from(["left", "center", "right"])

# 模板名称策略 - 避免空字符串和特殊字符
template_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_- '),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# 完整配置策略
config_strategy = st.fixed_dictionaries({
    "dpi": st.integers(min_value=72, max_value=2400),
    "width_mm": st.one_of(st.none(), st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False)),
    "height_mm": st.one_of(st.none(), st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False)),
    "width_px": st.one_of(st.none(), st.integers(min_value=100, max_value=5000)),
    "height_px": st.one_of(st.none(), st.integers(min_value=100, max_value=5000)),
    "lock_aspect_ratio": st.booleans(),
    "color_mode": color_mode_strategy,
    "foreground_color": color_strategy,
    "background_color": color_strategy,
    "font_family": st.sampled_from(["Arial", "Times New Roman", "Helvetica", "Courier"]),
    "font_size": st.integers(min_value=6, max_value=72),
    "letter_spacing": st.floats(min_value=-5.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    "isbn_text_offset_y": st.integers(min_value=0, max_value=50),
    "digits_offset_y": st.integers(min_value=0, max_value=50),
    "text_alignment": text_alignment_strategy
})


class TestTemplateRoundTrip:
    """Property 14: 模板Round-Trip
    
    **Feature: isbn-barcode-generator, Property 14: 模板Round-Trip**
    **Validates: Requirements 12.1, 12.2, 12.3**
    
    *For any* 有效的配置对象，保存为模板后再加载，加载的配置应与原始配置完全一致。
    """
    
    @pytest.fixture(autouse=True)
    def setup_temp_dir(self):
        """为每个测试创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        yield
        # 清理临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @given(name=template_name_strategy, config=config_strategy)
    @settings(max_examples=100)
    def test_save_then_load_returns_equivalent_config(self, name: str, config: dict):
        """保存模板后再加载，配置应完全一致
        
        **Feature: isbn-barcode-generator, Property 14: 模板Round-Trip**
        **Validates: Requirements 12.1, 12.2, 12.3**
        """
        manager = TemplateManager(self.temp_dir)
        
        # 保存模板
        manager.save_template(name, config)
        
        # 加载模板
        loaded_config = manager.load_template(name)
        
        # 验证所有配置项一致
        for key, original_value in config.items():
            loaded_value = loaded_config.get(key)
            
            # 处理颜色值（元组 vs 列表）
            if key in ('foreground_color', 'background_color'):
                assert tuple(loaded_value) == tuple(original_value), \
                    f"Color mismatch for {key}: {loaded_value} != {original_value}"
            # 处理浮点数比较
            elif isinstance(original_value, float):
                if original_value is None:
                    assert loaded_value is None
                else:
                    assert abs(loaded_value - original_value) < 1e-9, \
                        f"Float mismatch for {key}: {loaded_value} != {original_value}"
            else:
                assert loaded_value == original_value, \
                    f"Value mismatch for {key}: {loaded_value} != {original_value}"


class TestTemplateManagerBasicOperations:
    """模板管理器基本操作测试"""
    
    @pytest.fixture(autouse=True)
    def setup_temp_dir(self):
        """为每个测试创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        yield
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_default_template_returns_valid_config(self):
        """默认模板应包含所有必要的配置项"""
        manager = TemplateManager(self.temp_dir)
        default = manager.get_default_template()
        
        # 验证必要的配置项存在
        assert "dpi" in default
        assert "color_mode" in default
        assert "foreground_color" in default
        assert "background_color" in default
        assert "font_family" in default
        assert "font_size" in default
        assert "lock_aspect_ratio" in default
        
        # 验证默认值合理
        assert default["dpi"] == 300
        assert default["color_mode"] == "BITMAP"
    
    def test_list_templates_empty_initially(self):
        """初始时模板列表应为空"""
        manager = TemplateManager(self.temp_dir)
        templates = manager.list_templates()
        assert templates == []
    
    def test_save_and_list_templates(self):
        """保存模板后应出现在列表中"""
        manager = TemplateManager(self.temp_dir)
        config = manager.get_default_template()
        
        manager.save_template("测试模板", config)
        
        templates = manager.list_templates()
        assert "测试模板" in templates
    
    def test_delete_template(self):
        """删除模板后应从列表中移除"""
        manager = TemplateManager(self.temp_dir)
        config = manager.get_default_template()
        
        manager.save_template("待删除模板", config)
        assert "待删除模板" in manager.list_templates()
        
        manager.delete_template("待删除模板")
        assert "待删除模板" not in manager.list_templates()
    
    def test_load_nonexistent_template_raises_error(self):
        """加载不存在的模板应抛出异常"""
        manager = TemplateManager(self.temp_dir)
        
        with pytest.raises(FileNotFoundError):
            manager.load_template("不存在的模板")
    
    def test_delete_nonexistent_template_raises_error(self):
        """删除不存在的模板应抛出异常"""
        manager = TemplateManager(self.temp_dir)
        
        with pytest.raises(FileNotFoundError):
            manager.delete_template("不存在的模板")
    
    def test_save_template_with_empty_name_raises_error(self):
        """保存空名称模板应抛出异常"""
        manager = TemplateManager(self.temp_dir)
        config = manager.get_default_template()
        
        with pytest.raises(ValueError):
            manager.save_template("", config)
        
        with pytest.raises(ValueError):
            manager.save_template("   ", config)
    
    def test_template_exists(self):
        """template_exists应正确检测模板是否存在"""
        manager = TemplateManager(self.temp_dir)
        config = manager.get_default_template()
        
        assert not manager.template_exists("测试模板")
        
        manager.save_template("测试模板", config)
        
        assert manager.template_exists("测试模板")
    
    def test_update_existing_template(self):
        """更新现有模板应保留创建时间"""
        manager = TemplateManager(self.temp_dir)
        config1 = manager.get_default_template()
        config1["dpi"] = 300
        
        manager.save_template("更新测试", config1)
        info1 = manager.get_template_info("更新测试")
        
        # 更新模板
        config2 = manager.get_default_template()
        config2["dpi"] = 600
        manager.save_template("更新测试", config2)
        info2 = manager.get_template_info("更新测试")
        
        # 创建时间应保持不变
        assert info1.created_at == info2.created_at
        # 更新时间应改变
        assert info1.updated_at != info2.updated_at
        # 配置应更新
        loaded = manager.load_template("更新测试")
        assert loaded["dpi"] == 600
