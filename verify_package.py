"""验证打包后的ZIP文件中的图片路径"""
import zipfile
import sys

zip_path = sys.argv[1] if len(sys.argv) > 1 else "data/output/2023CVPR-CoMFormer/2023CVPR-CoMFormer_dita_package.zip"

with zipfile.ZipFile(zip_path, 'r') as z:
    # 检查一个包含图片的DITA文件
    dita_file = "005_concept_3_2__Comformer_Architecture.dita"
    if dita_file in z.namelist():
        content = z.read(dita_file).decode('utf-8')
        if 'href="images/' in content:
            print("[SUCCESS] 图片路径已正确修正为: images/xxx.png")
            # 提取图片路径
            import re
            paths = re.findall(r'href="images/([^"]+)"', content)
            if paths:
                print(f"  找到的图片路径: {paths[0]}")
        elif '../images/' in content:
            print("[ERROR] 图片路径仍然是 ../images/，未修正")
        else:
            print("[WARNING] 未找到图片路径引用")
    else:
        print(f"[ERROR] 未找到文件: {dita_file}")
    
    # 列出所有文件
    print(f"\nZIP文件内容 ({len(z.namelist())} 个文件):")
    dita_files = [f for f in z.namelist() if f.endswith('.dita')]
    image_files = [f for f in z.namelist() if f.endswith(('.png', '.jpg', '.jpeg'))]
    print(f"  - DITA文件: {len(dita_files)} 个")
    print(f"  - 图片文件: {len(image_files)} 个")
    if image_files:
        print(f"  示例: {image_files[0]}")







