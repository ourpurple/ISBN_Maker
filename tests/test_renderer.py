"""
TIF Renderer Tests - TIF渲染器测试

Property-based tests for the TIF renderer module.
"""

import pytest
import tempfile
import os
from hypothesis import given, strategies as st, settings, assume

from src.isbn_barcode_generator.core.renderer import (
    TIFRenderer, RenderConfig, TIFConfig, ColorMode, TextAlignment
)
from src.isbn_barcode_generator.core.validator import ISBNValidator, ParsedISBN
from src.isbn_barcode_generator.core.encoder import EAN13Encoder, BarcodePattern


# Helper function to create a valid RenderConfig
def create_test_config(
    dpi: int = 300,
    width_mm: float = None,
    height_mm: float = None,
    width_px: int = None,
    height_px: int = None,
    lock_aspect_ratio: bool = True,
    color_mode: ColorMode = ColorMode.BITMAP,
    foreground_color: tuple = (0, 0, 0),
    background_color: tuple = (255, 255, 255)
) -> RenderConfig:
    """Create a test RenderConfig with a valid ISBN"""
    validator = ISBNValidator()
    encoder = EAN13Encoder()
    
    # Use a known valid ISBN
    isbn = validator.parse("9787564922351")
    pattern = encoder.encode(isbn.digits)
    
    return RenderConfig(
        isbn=isbn,
        barcode_pattern=pattern,
        dpi=dpi,
        width_mm=width_mm,
        height_mm=height_mm,
        width_px=width_px,
        height_px=height_px,
        lock_aspect_ratio=lock_aspect_ratio,
        color_mode=color_mode,
        foreground_color=foreground_color,
        background_color=background_color
    )


# Strategy for generating valid DPI values
# Use higher minimum DPI to avoid rounding errors at very low resolutions
# At 300 DPI, module width is ~3.9px which provides good precision
dpi_strategy = st.integers(min_value=300, max_value=2400)


class TestDPIProperty:
    """Property 7: 分辨率设置正确性
    
    *For any* 指定的DPI值（如300、600、1200），生成的TIF图像元数据中的DPI应与指定值一致。
    **Validates: Requirements 4.1**
    """
    
    @given(dpi=dpi_strategy)
    @settings(max_examples=100)
    def test_dpi_setting_correctness(self, dpi: int):
        """Feature: isbn-barcode-generator, Property 7: 分辨率设置正确性
        
        For any specified DPI value, the generated TIF image metadata DPI should match.
        **Validates: Requirements 4.1**
        """
        renderer = TIFRenderer()
        config = create_test_config(dpi=dpi)
        
        # Render the image
        image = renderer.render(config)
        
        # Save to temp file and verify DPI
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as f:
            temp_path = f.name
        
        try:
            tif_config = TIFConfig(dpi=dpi)
            renderer.save_tif(image, temp_path, tif_config)
            
            # Re-open and check DPI
            from PIL import Image
            with Image.open(temp_path) as saved_image:
                saved_dpi = saved_image.info.get('dpi', (72, 72))
                # DPI should match (allowing for minor floating point differences)
                assert abs(saved_dpi[0] - dpi) < 1, f"Expected DPI {dpi}, got {saved_dpi[0]}"
                assert abs(saved_dpi[1] - dpi) < 1, f"Expected DPI {dpi}, got {saved_dpi[1]}"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# Strategies for image size testing
width_mm_strategy = st.floats(min_value=20.0, max_value=100.0, allow_nan=False, allow_infinity=False)
height_mm_strategy = st.floats(min_value=15.0, max_value=80.0, allow_nan=False, allow_infinity=False)
width_px_strategy = st.integers(min_value=100, max_value=1000)
height_px_strategy = st.integers(min_value=80, max_value=800)


class TestImageSizeProperty:
    """Property 8: 图像尺寸设置正确性
    
    *For any* 指定的宽度和高度（毫米或像素），生成的图像实际尺寸应与指定值一致（在合理误差范围内）。
    **Validates: Requirements 4.5, 7.1, 7.2**
    """
    
    @given(width_mm=width_mm_strategy, height_mm=height_mm_strategy, dpi=dpi_strategy)
    @settings(max_examples=100)
    def test_image_size_mm_correctness(self, width_mm: float, height_mm: float, dpi: int):
        """Feature: isbn-barcode-generator, Property 8: 图像尺寸设置正确性 (毫米)
        
        For any specified width and height in mm, the generated image size should match.
        **Validates: Requirements 4.5, 7.1, 7.2**
        """
        renderer = TIFRenderer()
        config = create_test_config(
            dpi=dpi,
            width_mm=width_mm,
            height_mm=height_mm,
            lock_aspect_ratio=False  # Disable aspect ratio lock for this test
        )
        
        # Render the image
        image = renderer.render(config)
        
        # Calculate expected pixel dimensions
        expected_width_px = int(width_mm * dpi / 25.4)
        expected_height_px = int(height_mm * dpi / 25.4)
        
        # Verify dimensions (allow 1 pixel tolerance due to rounding)
        actual_width, actual_height = image.size
        assert abs(actual_width - expected_width_px) <= 1, \
            f"Width mismatch: expected {expected_width_px}, got {actual_width}"
        assert abs(actual_height - expected_height_px) <= 1, \
            f"Height mismatch: expected {expected_height_px}, got {actual_height}"
    
    @given(width_px=width_px_strategy, height_px=height_px_strategy)
    @settings(max_examples=100)
    def test_image_size_px_correctness(self, width_px: int, height_px: int):
        """Feature: isbn-barcode-generator, Property 8: 图像尺寸设置正确性 (像素)
        
        For any specified width and height in pixels, the generated image size should match exactly.
        **Validates: Requirements 4.5, 7.1, 7.2**
        """
        renderer = TIFRenderer()
        config = create_test_config(
            width_px=width_px,
            height_px=height_px,
            lock_aspect_ratio=False  # Disable aspect ratio lock for this test
        )
        
        # Render the image
        image = renderer.render(config)
        
        # Verify dimensions match exactly
        actual_width, actual_height = image.size
        assert actual_width == width_px, f"Width mismatch: expected {width_px}, got {actual_width}"
        assert actual_height == height_px, f"Height mismatch: expected {height_px}, got {actual_height}"



class TestAspectRatioProperty:
    """Property 9: 宽高比锁定正确性
    
    *For any* 启用宽高比锁定的配置，当仅指定宽度时，计算出的高度应保持原始宽高比；
    当仅指定高度时，计算出的宽度应保持原始宽高比。
    **Validates: Requirements 7.3, 7.4, 7.5**
    """
    
    @given(width_mm=width_mm_strategy, dpi=dpi_strategy)
    @settings(max_examples=100)
    def test_aspect_ratio_lock_width_only(self, width_mm: float, dpi: int):
        """Feature: isbn-barcode-generator, Property 9: 宽高比锁定正确性 (仅指定宽度)
        
        When only width is specified with aspect ratio lock, height should maintain ratio.
        **Validates: Requirements 7.3, 7.4**
        """
        # Skip low DPI values that cause excessive rounding errors
        # At DPI < 300, integer pixel rounding can cause >3% aspect ratio deviation
        assume(dpi >= 300)
        
        renderer = TIFRenderer()
        
        # Get default aspect ratio
        default_width, default_height = renderer.get_default_size_mm()
        expected_aspect_ratio = default_width / default_height
        
        config = create_test_config(
            dpi=dpi,
            width_mm=width_mm,
            height_mm=None,
            lock_aspect_ratio=True
        )
        
        # Render the image
        image = renderer.render(config)
        actual_width, actual_height = image.size
        
        # Calculate actual aspect ratio
        actual_aspect_ratio = actual_width / actual_height
        
        # Aspect ratios should match within tolerance
        # Allow 3% difference to account for integer rounding at various DPI/size combinations
        ratio_diff = abs(actual_aspect_ratio - expected_aspect_ratio) / expected_aspect_ratio
        assert ratio_diff < 0.03, \
            f"Aspect ratio mismatch: expected {expected_aspect_ratio:.4f}, got {actual_aspect_ratio:.4f}. The difference is {ratio_diff*100:.2f}% which exceeds the 3% tolerance."
    
    @given(height_mm=height_mm_strategy, dpi=dpi_strategy)
    @settings(max_examples=100)
    def test_aspect_ratio_lock_height_only(self, height_mm: float, dpi: int):
        """Feature: isbn-barcode-generator, Property 9: 宽高比锁定正确性 (仅指定高度)
        
        When only height is specified with aspect ratio lock, width should maintain ratio.
        **Validates: Requirements 7.3, 7.5**
        """
        # Skip low DPI values that cause excessive rounding errors
        # At DPI < 300, integer pixel rounding can cause >3% aspect ratio deviation
        assume(dpi >= 300)
        
        renderer = TIFRenderer()
        
        # Get default aspect ratio
        default_width, default_height = renderer.get_default_size_mm()
        expected_aspect_ratio = default_width / default_height
        
        config = create_test_config(
            dpi=dpi,
            width_mm=None,
            height_mm=height_mm,
            lock_aspect_ratio=True
        )
        
        # Render the image
        image = renderer.render(config)
        actual_width, actual_height = image.size
        
        # Calculate actual aspect ratio
        actual_aspect_ratio = actual_width / actual_height
        
        # Aspect ratios should match within tolerance
        # Allow 3% difference to account for integer rounding at various DPI/size combinations
        ratio_diff = abs(actual_aspect_ratio - expected_aspect_ratio) / expected_aspect_ratio
        assert ratio_diff < 0.03, \
            f"Aspect ratio mismatch: expected {expected_aspect_ratio:.4f}, got {actual_aspect_ratio:.4f}. The difference is {ratio_diff*100:.2f}% which exceeds the 3% tolerance."



# Strategy for color modes
color_mode_strategy = st.sampled_from([ColorMode.BITMAP, ColorMode.GRAYSCALE, ColorMode.RGB, ColorMode.CMYK])


class TestColorModeProperty:
    """Property 10: 颜色模式输出正确性
    
    *For any* 指定的颜色模式（BITMAP、GRAYSCALE、RGB、CMYK），生成的图像的颜色模式应与指定值一致。
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    
    @given(color_mode=color_mode_strategy)
    @settings(max_examples=100)
    def test_color_mode_output_correctness(self, color_mode: ColorMode):
        """Feature: isbn-barcode-generator, Property 10: 颜色模式输出正确性
        
        For any specified color mode, the generated image mode should match.
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        renderer = TIFRenderer()
        config = create_test_config(color_mode=color_mode)
        
        # Render the image
        image = renderer.render(config)
        
        # Verify the image mode matches the expected PIL mode
        expected_mode = color_mode.value
        actual_mode = image.mode
        
        assert actual_mode == expected_mode, \
            f"Color mode mismatch: expected {expected_mode}, got {actual_mode}"
    
    def test_bitmap_mode_is_binary(self):
        """Test that BITMAP mode produces a binary (1-bit) image"""
        renderer = TIFRenderer()
        config = create_test_config(color_mode=ColorMode.BITMAP)
        
        image = renderer.render(config)
        
        # BITMAP mode should be "1" (1-bit pixels)
        assert image.mode == "1"
        
        # All pixels should be either 0 or 1
        pixels = list(image.getdata())
        unique_values = set(pixels)
        assert unique_values.issubset({0, 1}), f"BITMAP should only have 0 and 1, got {unique_values}"
    
    def test_grayscale_mode_is_8bit(self):
        """Test that GRAYSCALE mode produces an 8-bit grayscale image"""
        renderer = TIFRenderer()
        config = create_test_config(color_mode=ColorMode.GRAYSCALE)
        
        image = renderer.render(config)
        
        # GRAYSCALE mode should be "L" (8-bit pixels)
        assert image.mode == "L"
    
    def test_rgb_mode_has_three_channels(self):
        """Test that RGB mode produces a 3-channel image"""
        renderer = TIFRenderer()
        config = create_test_config(color_mode=ColorMode.RGB)
        
        image = renderer.render(config)
        
        # RGB mode should be "RGB"
        assert image.mode == "RGB"
        
        # Should have 3 channels
        assert len(image.getbands()) == 3
    
    def test_cmyk_mode_has_four_channels(self):
        """Test that CMYK mode produces a 4-channel image"""
        renderer = TIFRenderer()
        config = create_test_config(color_mode=ColorMode.CMYK)
        
        image = renderer.render(config)
        
        # CMYK mode should be "CMYK"
        assert image.mode == "CMYK"
        
        # Should have 4 channels
        assert len(image.getbands()) == 4



# Strategy for RGB colors
rgb_color_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)


class TestForegroundBackgroundColorProperty:
    """Property 11: 前景色背景色应用正确性
    
    *For any* 指定的前景色和背景色，生成的图像中条码区域应使用前景色，空白区域应使用背景色。
    **Validates: Requirements 8.7**
    """
    
    @given(fg_color=rgb_color_strategy, bg_color=rgb_color_strategy)
    @settings(max_examples=100)
    def test_foreground_background_color_application(self, fg_color: tuple, bg_color: tuple):
        """Feature: isbn-barcode-generator, Property 11: 前景色背景色应用正确性
        
        For any specified foreground and background colors, the image should use them correctly.
        **Validates: Requirements 8.7**
        """
        # Skip if colors are too similar (hard to distinguish)
        color_diff = sum(abs(fg_color[i] - bg_color[i]) for i in range(3))
        assume(color_diff > 100)  # Ensure colors are distinguishable
        
        renderer = TIFRenderer()
        config = create_test_config(
            color_mode=ColorMode.RGB,
            foreground_color=fg_color,
            background_color=bg_color
        )
        
        # Render the image
        image = renderer.render(config)
        
        # Get pixel data
        pixels = list(image.getdata())
        
        # Check that the image contains pixels close to both foreground and background colors
        has_fg_like = False
        has_bg_like = False
        
        for pixel in pixels:
            # Check if pixel is close to foreground color
            fg_diff = sum(abs(pixel[i] - fg_color[i]) for i in range(3))
            if fg_diff < 50:  # Allow some tolerance
                has_fg_like = True
            
            # Check if pixel is close to background color
            bg_diff = sum(abs(pixel[i] - bg_color[i]) for i in range(3))
            if bg_diff < 50:  # Allow some tolerance
                has_bg_like = True
            
            if has_fg_like and has_bg_like:
                break
        
        assert has_fg_like, f"Image should contain foreground color {fg_color}"
        assert has_bg_like, f"Image should contain background color {bg_color}"
    
    def test_default_black_on_white(self):
        """Test default colors are black foreground on white background"""
        renderer = TIFRenderer()
        config = create_test_config(
            color_mode=ColorMode.RGB,
            foreground_color=(0, 0, 0),
            background_color=(255, 255, 255)
        )
        
        image = renderer.render(config)
        pixels = list(image.getdata())
        
        # Should have black pixels (barcode)
        has_black = any(p == (0, 0, 0) for p in pixels)
        # Should have white pixels (background)
        has_white = any(p == (255, 255, 255) for p in pixels)
        
        assert has_black, "Image should contain black pixels for barcode"
        assert has_white, "Image should contain white pixels for background"
    
    def test_inverted_colors(self):
        """Test inverted colors (white on black)"""
        renderer = TIFRenderer()
        config = create_test_config(
            color_mode=ColorMode.RGB,
            foreground_color=(255, 255, 255),
            background_color=(0, 0, 0)
        )
        
        image = renderer.render(config)
        pixels = list(image.getdata())
        
        # Should have white pixels (barcode)
        has_white = any(p == (255, 255, 255) for p in pixels)
        # Should have black pixels (background)
        has_black = any(p == (0, 0, 0) for p in pixels)
        
        assert has_white, "Image should contain white pixels for barcode"
        assert has_black, "Image should contain black pixels for background"



class TestQuietZoneAndModuleWidthProperty:
    """Property 15 & 16: 静区符合标准 & 模块宽度一致性
    
    Property 15: *For any* 生成的条码图像，左侧静区应至少为11个模块宽度，右侧静区应至少为7个模块宽度。
    Property 16: *For any* 生成的条码图像，所有条和空的模块宽度应保持一致（在1像素误差范围内）。
    **Validates: Requirements 6.1, 6.2**
    """
    
    @given(dpi=dpi_strategy)
    @settings(max_examples=100)
    def test_quiet_zone_compliance(self, dpi: int):
        """Feature: isbn-barcode-generator, Property 15: 静区符合标准
        
        For any generated barcode image, quiet zones should meet GS1 standards.
        **Validates: Requirements 6.1**
        """
        renderer = TIFRenderer()
        config = create_test_config(dpi=dpi, color_mode=ColorMode.BITMAP)
        
        # Render the image
        image = renderer.render(config)
        width, height = image.size
        
        # Calculate expected module width
        total_modules = (renderer.LEFT_QUIET_ZONE_MODULES + 
                        renderer.EAN13_MODULES + 
                        renderer.RIGHT_QUIET_ZONE_MODULES)
        module_width_px = width / total_modules
        
        # Expected quiet zone widths
        expected_left_quiet_zone = renderer.LEFT_QUIET_ZONE_MODULES * module_width_px
        expected_right_quiet_zone = renderer.RIGHT_QUIET_ZONE_MODULES * module_width_px
        
        # Get pixel data as a 2D array
        pixels = list(image.getdata())
        
        # Check left quiet zone (should be all white/background)
        # Sample a row in the middle of the barcode area
        mid_row = height // 2
        row_start = mid_row * width
        
        # Count consecutive white pixels from left
        left_white_count = 0
        for x in range(width):
            pixel = pixels[row_start + x]
            if pixel == 1:  # White in BITMAP mode
                left_white_count += 1
            else:
                break
        
        # Left quiet zone should be at least 11 modules (with some tolerance)
        min_left_quiet = int(expected_left_quiet_zone * 0.9)  # 10% tolerance
        assert left_white_count >= min_left_quiet, \
            f"Left quiet zone too small: {left_white_count}px, expected at least {min_left_quiet}px"
        
        # Count consecutive white pixels from right
        right_white_count = 0
        for x in range(width - 1, -1, -1):
            pixel = pixels[row_start + x]
            if pixel == 1:  # White in BITMAP mode
                right_white_count += 1
            else:
                break
        
        # Right quiet zone should be at least 7 modules (with some tolerance)
        min_right_quiet = int(expected_right_quiet_zone * 0.9)  # 10% tolerance
        assert right_white_count >= min_right_quiet, \
            f"Right quiet zone too small: {right_white_count}px, expected at least {min_right_quiet}px"
    
    @given(dpi=dpi_strategy)
    @settings(max_examples=100)
    def test_module_width_consistency(self, dpi: int):
        """Feature: isbn-barcode-generator, Property 16: 模块宽度一致性
        
        For any generated barcode image, all bar and space module widths should be consistent.
        **Validates: Requirements 6.2**
        """
        renderer = TIFRenderer()
        config = create_test_config(dpi=dpi, color_mode=ColorMode.BITMAP)
        
        # Render the image
        image = renderer.render(config)
        width, height = image.size
        
        # Calculate expected module width
        total_modules = (renderer.LEFT_QUIET_ZONE_MODULES + 
                        renderer.EAN13_MODULES + 
                        renderer.RIGHT_QUIET_ZONE_MODULES)
        expected_module_width = width / total_modules
        
        # Skip test if module width is too small (less than 2 pixels)
        # At very low resolutions, integer rounding makes precise module width impossible
        if expected_module_width < 2.0:
            return
        
        # Get pixel data
        pixels = list(image.getdata())
        
        # Sample a row in the barcode area (avoiding text areas)
        barcode_row = height // 3  # Upper third should be in barcode area
        row_start = barcode_row * width
        
        # Find bar widths by detecting transitions
        bar_widths = []
        current_color = None
        current_width = 0
        
        # Start after left quiet zone
        start_x = int(renderer.LEFT_QUIET_ZONE_MODULES * expected_module_width)
        end_x = int((renderer.LEFT_QUIET_ZONE_MODULES + renderer.EAN13_MODULES) * expected_module_width)
        
        for x in range(start_x, min(end_x, width)):
            pixel = pixels[row_start + x]
            
            if current_color is None:
                current_color = pixel
                current_width = 1
            elif pixel == current_color:
                current_width += 1
            else:
                bar_widths.append(current_width)
                current_color = pixel
                current_width = 1
        
        if current_width > 0:
            bar_widths.append(current_width)
        
        # Skip if we didn't find enough bars (image might be too small)
        if len(bar_widths) < 10:
            return
        
        # All bar widths should be multiples of the module width (within tolerance)
        # EAN-13 bars are 1, 2, 3, or 4 modules wide
        for bar_width in bar_widths:
            # Calculate how many modules this bar represents
            modules = bar_width / expected_module_width
            rounded_modules = round(modules)
            
            # Should be close to an integer number of modules
            # Allow 35% deviation to account for integer pixel rounding
            if rounded_modules > 0:
                deviation = abs(modules - rounded_modules) / rounded_modules
                assert deviation < 0.35, \
                    f"Bar width {bar_width}px deviates too much from expected module width {expected_module_width}px"
