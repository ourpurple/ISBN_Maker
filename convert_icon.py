"""
图标转换脚本

将图片转换为程序图标格式（.ico 和 .png）
使用方法：
1. 将你的图标图片保存为 icon_source.png（放在项目根目录）
2. 运行此脚本：python convert_icon.py
"""

from PIL import Image
import os

def convert_to_icon(source_path: str, output_dir: str):
    """将图片转换为多种尺寸的图标"""
    
    if not os.path.exists(source_path):
        print(f"错误：找不到源图片 {source_path}")
        print("请将你的图标图片保存为 icon_source.png 后重新运行此脚本")
        return False
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 打开源图片
    img = Image.open(source_path)
    
    # 转换为 RGBA 模式（支持透明度）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 生成 PNG 图标（256x256）
    png_path = os.path.join(output_dir, "icon.png")
    img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    img_256.save(png_path, "PNG")
    print(f"已生成 PNG 图标: {png_path}")
    
    # 生成 ICO 文件（包含多种尺寸）
    ico_path = os.path.join(output_dir, "icon.ico")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # 保存 ICO 文件
    icons[0].save(ico_path, format='ICO', sizes=[(s[0], s[1]) for s in sizes], 
                  append_images=icons[1:])
    print(f"已生成 ICO 图标: {ico_path}")
    
    return True


if __name__ == "__main__":
    source = "icon_source.png"
    output = "src/isbn_barcode_generator/resources"
    
    print("=" * 50)
    print("ISBN条码生成器 - 图标转换工具")
    print("=" * 50)
    
    if convert_to_icon(source, output):
        print("\n图标转换完成！")
        print("程序启动时将自动加载新图标。")
    else:
        print("\n请按以下步骤操作：")
        print("1. 将你的图标图片保存为 'icon_source.png'（放在项目根目录）")
        print("2. 重新运行此脚本：python convert_icon.py")
