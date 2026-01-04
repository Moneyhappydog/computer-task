"""
DITA文件打包工具
将Layer3生成的DITA文件和相关的图片资源一起打包成ZIP文件
"""
import zipfile
import argparse
from pathlib import Path
import logging
from typing import List, Set
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_image_paths_from_dita(dita_file: Path) -> Set[str]:
    """
    从DITA文件中提取所有图片路径引用
    
    Args:
        dita_file: DITA文件路径
        
    Returns:
        图片路径集合（相对路径，如 "../images/page_4_image_0.png"）
    """
    image_paths = set()
    
    try:
        with open(dita_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配 <image href="..." /> 或 <image href="..."></image>
        # 也匹配 href="../images/xxx.png" 格式
        patterns = [
            r'<image\s+[^>]*href=["\']([^"\']+)["\']',
            r'href=["\']([^"\']*images[^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # 清理路径
                path = match.strip()
                if path and ('images' in path.lower() or path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))):
                    image_paths.add(path)
        
        logger.debug(f"从 {dita_file.name} 中提取到 {len(image_paths)} 个图片引用")
        
    except Exception as e:
        logger.warning(f"读取DITA文件失败 {dita_file}: {e}")
    
    return image_paths


def resolve_image_path(image_path: str, dita_file: Path, base_dir: Path) -> Path:
    """
    解析图片路径，将相对路径转换为绝对路径
    
    Args:
        image_path: 图片相对路径（如 "../images/page_4_image_0.png"）
        dita_file: DITA文件路径（用于计算相对路径的基准）
        base_dir: 基础目录（通常是 output/{doc_name}/）
        
    Returns:
        图片的绝对路径
    """
    # 清理路径
    image_path = image_path.strip()
    
    # 如果是绝对路径，直接返回
    if Path(image_path).is_absolute():
        return Path(image_path)
    
    # 处理相对路径
    # 如果路径以 ../ 开头，从 base_dir 的父目录开始
    if image_path.startswith('../'):
        # 移除 ../ 前缀
        relative_path = image_path[3:]
        # 从 base_dir 的父目录解析
        resolved = base_dir.parent / relative_path
    elif image_path.startswith('./'):
        # 移除 ./ 前缀
        relative_path = image_path[2:]
        resolved = base_dir / relative_path
    else:
        # 相对于 base_dir
        resolved = base_dir / image_path
    
    return resolved


def package_dita(
    layer3_dir: Path,
    output_zip: Path = None,
    include_all_images: bool = True
) -> Path:
    """
    打包DITA文件和图片资源
    
    Args:
        layer3_dir: Layer3输出目录（包含.dita文件）
        output_zip: 输出ZIP文件路径（如果为None，自动生成）
        include_all_images: 是否包含所有图片（True）或仅包含引用的图片（False）
        
    Returns:
        生成的ZIP文件路径
    """
    layer3_dir = Path(layer3_dir)
    
    if not layer3_dir.exists():
        raise FileNotFoundError(f"Layer3目录不存在: {layer3_dir}")
    
    # 查找所有DITA文件
    dita_files = list(layer3_dir.glob("*.dita"))
    if not dita_files:
        raise ValueError(f"在 {layer3_dir} 中未找到DITA文件")
    
    logger.info(f"找到 {len(dita_files)} 个DITA文件")
    
    # 确定基础目录（通常是 layer3_dir 的父目录）
    base_dir = layer3_dir.parent
    
    # 确定图片目录
    images_dir = base_dir / "images"
    
    # 收集需要打包的图片
    image_files_to_package = set()
    
    if include_all_images:
        # 包含所有图片
        if images_dir.exists():
            image_files = list(images_dir.glob("*.*"))
            image_files = [f for f in image_files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg']]
            image_files_to_package = set(image_files)
            logger.info(f"包含所有图片: {len(image_files_to_package)} 个文件")
        else:
            logger.warning(f"图片目录不存在: {images_dir}")
    else:
        # 仅包含引用的图片
        all_image_paths = set()
        for dita_file in dita_files:
            image_paths = extract_image_paths_from_dita(dita_file)
            all_image_paths.update(image_paths)
        
        logger.info(f"从DITA文件中提取到 {len(all_image_paths)} 个图片引用")
        
        # 解析每个图片路径
        for image_path in all_image_paths:
            resolved_path = resolve_image_path(image_path, dita_file, base_dir)
            if resolved_path.exists():
                image_files_to_package.add(resolved_path)
                logger.debug(f"找到图片: {resolved_path}")
            else:
                logger.warning(f"图片文件不存在: {resolved_path} (引用路径: {image_path})")
    
    # 生成输出ZIP文件名
    if output_zip is None:
        doc_name = base_dir.name
        output_zip = base_dir / f"{doc_name}_dita_package.zip"
    
    output_zip = Path(output_zip)
    
    # 创建ZIP文件
    logger.info(f"开始打包到: {output_zip}")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加所有DITA文件（并修正图片路径）
        for dita_file in dita_files:
            # 读取DITA文件内容
            with open(dita_file, 'r', encoding='utf-8') as f:
                dita_content = f.read()
            
            # 修正图片路径：将 ../images/ 改为 images/
            # 匹配 href="../images/xxx" 或 href='../images/xxx'
            import re
            dita_content = re.sub(
                r'href=["\']\.\./images/([^"\']+)["\']',
                r'href="images/\1"',
                dita_content
            )
            
            # 在ZIP中保持相对路径结构
            arcname = dita_file.name
            # 将修正后的内容写入ZIP
            zipf.writestr(arcname, dita_content)
            logger.debug(f"添加DITA文件: {arcname} (已修正图片路径)")
        
        # 添加图片文件
        if image_files_to_package:
            # 在ZIP中创建 images/ 目录结构
            for image_file in image_files_to_package:
                # 计算在ZIP中的路径
                # 如果图片在 base_dir/images/ 下，在ZIP中应该是 images/filename
                if images_dir in image_file.parents or image_file.parent == images_dir:
                    # 图片在 images 目录下
                    arcname = f"images/{image_file.name}"
                else:
                    # 保持相对路径结构
                    try:
                        arcname = image_file.relative_to(base_dir)
                        arcname = str(arcname).replace('\\', '/')
                    except ValueError:
                        # 如果无法计算相对路径，使用文件名
                        arcname = f"images/{image_file.name}"
                
                zipf.write(image_file, arcname)
                logger.debug(f"添加图片: {arcname}")
        
        # 添加 layer3_result.json（如果存在）
        result_json = layer3_dir / "layer3_result.json"
        if result_json.exists():
            zipf.write(result_json, "layer3_result.json")
            logger.debug("添加 layer3_result.json")
    
    logger.info(f"✅ 打包完成: {output_zip}")
    logger.info(f"   - DITA文件: {len(dita_files)} 个")
    logger.info(f"   - 图片文件: {len(image_files_to_package)} 个")
    logger.info(f"   - ZIP大小: {output_zip.stat().st_size / 1024 / 1024:.2f} MB")
    
    return output_zip


def main():
    parser = argparse.ArgumentParser(
        description='打包DITA文件和图片资源',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 打包指定目录的DITA文件（包含所有图片）
  python package_dita.py data/output/2023CVPR-CoMFormer/layer3
  
  # 仅包含引用的图片
  python package_dita.py data/output/2023CVPR-CoMFormer/layer3 --only-referenced
  
  # 指定输出ZIP文件
  python package_dita.py data/output/2023CVPR-CoMFormer/layer3 -o output.zip
        """
    )
    
    parser.add_argument(
        'layer3_dir',
        type=str,
        help='Layer3输出目录路径（包含.dita文件）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出ZIP文件路径（默认: {doc_name}_dita_package.zip）'
    )
    
    parser.add_argument(
        '--only-referenced',
        action='store_true',
        help='仅包含DITA文件中引用的图片（默认: 包含所有图片）'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        layer3_dir = Path(args.layer3_dir)
        output_zip = Path(args.output) if args.output else None
        
        zip_file = package_dita(
            layer3_dir=layer3_dir,
            output_zip=output_zip,
            include_all_images=not args.only_referenced
        )
        
        print(f"\n[SUCCESS] 打包成功!")
        print(f"   ZIP文件: {zip_file}")
        print(f"   绝对路径: {zip_file.absolute()}")
        
    except Exception as e:
        logger.error(f"❌ 打包失败: {e}", exc_info=args.verbose)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

