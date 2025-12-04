"""
图片提取器
从 PDF 和 Word 文档中提取图片，并修正 Markdown 中的图片路径
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import re
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ImageExtractor:
    """图片提取与路径管理器"""
    
    def __init__(self, output_base_dir: Path = None):
        """
        初始化图片提取器
        
        Args:
            output_base_dir: 图片输出根目录，默认为 data/output
        """
        if output_base_dir is None:
            from src.utils.config import Config
            output_base_dir = Config.OUTPUT_DIR
        
        self.output_base_dir = Path(output_base_dir)
        logger.info("✅ 图片提取器初始化完成")
    
    def extract_and_save_images(
        self,
        images: Dict,
        doc_name: str
    ) -> Dict[str, Any]:
        """
        提取并保存图片到磁盘
        
        Args:
            images: 图片数据字典
                    - Marker格式: {page_num: [PIL.Image, ...], ...}
                    - Word格式: {image_id: PIL.Image, ...}
            doc_name: 文档名称（不含扩展名），用作文件夹名
        
        Returns:
            {
                'image_mapping': {'0_image_0': 'relative/path/to/image.png', ...},
                'image_dir': '/absolute/path/to/images',
                'total_images': 5,
                'saved_images': 5,
                'failed_images': 0
            }
        """
        logger.info(f"开始提取图片: 文档={doc_name}")
        
        # 创建图片输出目录: data/output/{doc_name}/images
        image_dir = self.output_base_dir / doc_name / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        
        image_mapping = {}
        saved_count = 0
        failed_count = 0
        total_count = 0
        
        # 统一处理：按 {page_num}_image_{idx}.png 格式命名
        logger.info("开始保存图片...")
        
        for page_num, page_images in images.items():
            # 将page_num转为int（如果是字符串）
            try:
                page_idx = int(page_num)
            except (ValueError, TypeError):
                page_idx = page_num
            
            # 确保是list
            if not isinstance(page_images, list):
                page_images = [page_images]
            
            for img_idx, image_obj in enumerate(page_images):
                total_count += 1
                
                # 生成文件名
                img_name = f"{page_idx}_image_{img_idx}"
                img_filename = f"{img_name}.png"
                img_path = image_dir / img_filename
                
                # 保存图片
                try:
                    self._save_image_object(image_obj, img_path)
                    
                    # 记录相对路径（相对于 Markdown 文件所在的 layer1 目录）
                    relative_path = f"../images/{img_filename}"
                    image_mapping[img_name] = relative_path
                    
                    saved_count += 1
                    logger.debug(f"已保存图片: {img_filename}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"保存图片失败 {img_filename}: {e}")
        
        result = {
            'image_mapping': image_mapping,
            'image_dir': str(image_dir),
            'relative_image_dir': f"{doc_name}/images",  # 相对路径
            'total_images': total_count,
            'saved_images': saved_count,
            'failed_images': failed_count
        }
        
        logger.info(f"✅ 图片提取完成: 总数={total_count}, 成功={saved_count}, 失败={failed_count}")
        
        return result
    
    def _save_image_object(self, image_obj: Any, output_path: Path):
        """
        保存图片对象到文件
        
        Args:
            image_obj: 图片对象（PIL.Image, bytes, 或其他格式）
            output_path: 输出文件路径
        """
        if isinstance(image_obj, Image.Image):
            # PIL Image 对象
            image_obj.save(output_path, 'PNG')
        
        elif hasattr(image_obj, 'save'):
            # 类似 PIL Image 的对象
            image_obj.save(output_path)
        
        elif isinstance(image_obj, bytes):
            # 字节数据
            try:
                img = Image.open(io.BytesIO(image_obj))
                img.save(output_path, 'PNG')
            except Exception:
                # 直接保存字节
                output_path.write_bytes(image_obj)
        
        elif hasattr(image_obj, 'read'):
            # 文件类对象
            img_data = image_obj.read()
            img = Image.open(io.BytesIO(img_data))
            img.save(output_path, 'PNG')
        
        else:
            raise ValueError(f"不支持的图片格式: {type(image_obj)}")
    
    def fix_markdown_image_paths(
        self,
        markdown_text: str,
        image_mapping: Dict[str, str],
        base_path: str = ""
    ) -> str:
        """
        修正 Markdown 中的图片路径
        
        Args:
            markdown_text: 原始 Markdown 文本
            image_mapping: 图片路径映射 {'0_image_0': 'session/images/0_image_0.png'}
            base_path: 基础路径前缀（可选）
        
        Returns:
            修正后的 Markdown 文本
        """
        if not image_mapping:
            return markdown_text
        
        logger.info(f"修正 Markdown 图片路径: {len(image_mapping)} 个图片")
        
        modified_text = markdown_text
        fixed_count = 0
        
        for img_name, new_path in image_mapping.items():
            # 添加基础路径（如果需要）
            full_path = f"{base_path}/{new_path}" if base_path else new_path
            
            # 匹配多种可能的图片引用格式
            patterns = [
                # Marker 格式: ![](0_image_0.png) 或 ![xxx](0_image_0.png)
                (f"!\\[.*?\\]\\({re.escape(img_name)}\\.png\\)", f"![Figure]({full_path})"),
                
                # 可能的其他格式: ![](0_image_0) 不带扩展名
                (f"!\\[.*?\\]\\({re.escape(img_name)}\\)", f"![Figure]({full_path})"),
                
                # HTML 格式: <img src="0_image_0.png">
                (f'<img\\s+src="{re.escape(img_name)}\\.png".*?>', f'<img src="{full_path}">'),
            ]
            
            for pattern, replacement in patterns:
                new_text = re.sub(pattern, replacement, modified_text)
                if new_text != modified_text:
                    fixed_count += 1
                    modified_text = new_text
                    logger.debug(f"已修正图片引用: {img_name}")
        
        logger.info(f"✅ 修正完成: {fixed_count} 个图片引用")
        
        return modified_text
    
    def get_image_statistics(self, image_mapping: Dict) -> Dict[str, Any]:
        """
        获取图片统计信息
        
        Args:
            image_mapping: 图片路径映射
        
        Returns:
            统计信息字典
        """
        total_images = len(image_mapping)
        
        # 按页码分组统计（针对 Marker 格式）
        page_distribution = {}
        for img_name in image_mapping.keys():
            if '_image_' in img_name:
                page_num = img_name.split('_image_')[0]
                page_distribution[page_num] = page_distribution.get(page_num, 0) + 1
        
        return {
            'total_images': total_images,
            'page_distribution': page_distribution,
            'pages_with_images': len(page_distribution)
        }


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("image_extractor")
    
    # 创建提取器
    extractor = ImageExtractor()
    
    print("📊 图片提取器测试")
    print("="*70)
    
    # 模拟 Marker 图片数据
    mock_marker_images = {
        0: [Image.new('RGB', (100, 100), color='red')],
        2: [
            Image.new('RGB', (100, 100), color='blue'),
            Image.new('RGB', (100, 100), color='green')
        ]
    }
    
    # 测试提取
    result = extractor.extract_and_save_images(
        mock_marker_images,
        doc_name="test_document"
    )
    
    print(f"\n✅ 提取结果:")
    print(f"  图片目录: {result['image_dir']}")
    print(f"  总图片数: {result['total_images']}")
    print(f"  成功保存: {result['saved_images']}")
    print(f"  图片映射: {result['image_mapping']}")
    
    # 测试路径修正
    mock_markdown = """
# Test Document

Here is an image: ![](0_image_0.png)

And another: ![Figure 1](2_image_0.png)

And one more: ![](2_image_1.png)
"""
    
    fixed_markdown = extractor.fix_markdown_image_paths(
        mock_markdown,
        result['image_mapping']
    )
    
    print(f"\n📝 修正后的 Markdown:")
    print(fixed_markdown)
    
    # 统计信息
    stats = extractor.get_image_statistics(result['image_mapping'])
    print(f"\n📈 统计信息:")
    print(f"  总图片数: {stats['total_images']}")
    print(f"  包含图片的页数: {stats['pages_with_images']}")
    print(f"  页码分布: {stats['page_distribution']}")
