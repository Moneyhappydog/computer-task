import os
import re

def check_resources(page_path):
    """
    检测给定页面是否有对应的图像和表格资源。

    Args:
        page_path (str): 页面文件路径，例如 'data/output/2023CVPR-CoMFormer/pages/page_1.md'

    Returns:
        dict: 包含检测结果的字典，例如：
              {
                  "images": ["path/to/0_image_0.png", "path/to/0_image_1.png"],
                  "tables": ["path/to/p6_table_1.png", "path/to/p6_table_2.png"]
              }
    """
    # 获取页面的目录和文件名
    page_dir = os.path.dirname(page_path)
    print(f"检查页面目录: {page_dir}")
    page_name = os.path.splitext(os.path.basename(page_path))[0]
    print(f"检查页面名称: {page_name}")
    
    # 提取页面编号
    page_match = re.search(r'page_(\d+)', page_name)
    if not page_match:
        print("无法从页面名称中提取页码")
        return {"images": [], "tables": []}
    
    page_num = int(page_match.group(1))
    print(f"页面编号: {page_num}")

    # 定义资源路径 - 使用 normpath 规范化路径
    base_dir = os.path.normpath(os.path.join(page_dir, ".."))
    image_dir = os.path.normpath(os.path.join(base_dir, "images"))
    table_dir = os.path.normpath(os.path.join(base_dir, "tables"))
    
    print(f"检查图像目录: {image_dir}")
    print(f"检查表格目录: {table_dir}")

    result = {
        "images": [],
        "tables": []
    }

    # 检查图像目录
    # 匹配模式: {page_num}_image_{序号}.png
    if os.path.exists(image_dir):
        for filename in os.listdir(image_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                # 匹配 {page_num}_image_{X}.png 格式
                match = re.match(rf'^{page_num}_image_(\d+)\.(png|jpg|jpeg)$', filename)
                if match:
                    image_path = os.path.join(image_dir, filename)
                    result["images"].append(image_path)
                    print(f"找到图像: {image_path}")
    
    # 检查表格目录
    # 匹配模式: p{page_num}_table_{序号}.png
    if os.path.exists(table_dir):
        for filename in os.listdir(table_dir):
            if filename.endswith(('.png', '.json')):
                # 匹配 p{page_num}_table_{X}.png 或 .json 格式
                match = re.match(rf'^p{page_num}_table_(\d+)\.(png|json)$', filename)
                if match:
                    table_path = os.path.join(table_dir, filename)
                    result["tables"].append(table_path)
                    print(f"找到表格: {table_path}")

    # 对结果按序号排序
    def get_index(path):
        match = re.search(r'_(\d+)\.(png|jpg|jpeg|json)$', os.path.basename(path))
        return int(match.group(1)) if match else 0
    
    result["images"].sort(key=get_index)
    result["tables"].sort(key=get_index)

    return result

if __name__ == "__main__":
    # 示例用法
    print("=" * 60)
    print("测试 page_2.md")
    print("=" * 60)
    test_page = "data/output/2023CVPR-CoMFormer/pages/page_2.md"
    result = check_resources(test_page)
    print(f"\n检测结果:")
    print(f"图像数量: {len(result['images'])}")
    print(f"表格数量: {len(result['tables'])}")
    if result['images']:
        print("\n图像:")
        for img in result['images']:
            print(f"  - {img}")
    if result['tables']:
        print("\n表格:")
        for tbl in result['tables']:
            print(f"  - {tbl}")
    
    print("\n" + "=" * 60)
    print("测试 page_0.md")
    print("=" * 60)
    test_page = "data/output/2023CVPR-CoMFormer/pages/page_0.md"
    result = check_resources(test_page)
    print(f"\n检测结果:")
    print(f"图像数量: {len(result['images'])}")
    print(f"表格数量: {len(result['tables'])}")
    if result['images']:
        print("\n图像:")
        for img in result['images']:
            print(f"  - {img}")
    if result['tables']:
        print("\n表格:")
        for tbl in result['tables']:
            print(f"  - {tbl}")
    
    print("\n" + "=" * 60)
    print("测试 page_6.md")
    print("=" * 60)
    test_page = "data/output/2023CVPR-CoMFormer/pages/page_6.md"
    result = check_resources(test_page)
    print(f"\n检测结果:")
    print(f"图像数量: {len(result['images'])}")
    print(f"表格数量: {len(result['tables'])}")
    if result['images']:
        print("\n图像:")
        for img in result['images']:
            print(f"  - {img}")
    if result['tables']:
        print("\n表格:")
        for tbl in result['tables']:
            print(f"  - {tbl}")