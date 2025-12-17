"""
自动下载公式检测模型
使用国内镜像站 hf-mirror.com，速度更快
下载到 HuggingFace 缓存目录，与 marker 等模型保持一致
支持断点续传
"""
import requests
from pathlib import Path
import os
import hashlib

def get_huggingface_cache_dir():
    """获取 HuggingFace 缓存目录"""
    # 优先使用环境变量
    cache_home = os.environ.get("HF_HOME")
    if cache_home:
        return Path(cache_home) / "hub"
    
    # 使用默认位置
    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        return Path(cache_home) / "huggingface" / "hub"
    
    # Windows/Mac/Linux 默认位置
    return Path.home() / ".cache" / "huggingface" / "hub"

def download_model():
    # 模型信息
    model_name = "arxivFormula_YOLOv8l.pt"
    repo_id = "LouiseBloch/ArxivFormulaYOLOv8"
    
    # 优先使用镜像站
    urls = [
        f"https://hf-mirror.com/{repo_id}/resolve/main/{model_name}",
        f"https://huggingface.co/{repo_id}/resolve/main/{model_name}",
    ]
    
    # 模拟 HuggingFace Hub 的缓存结构
    # 格式: models--{org}--{repo}/snapshots/{revision}/{filename}
    cache_dir = get_huggingface_cache_dir()
    repo_cache_dir = cache_dir / f"models--{repo_id.replace('/', '--')}"
    snapshots_dir = repo_cache_dir / "snapshots"
    
    # 使用 main 作为 revision
    snapshot_dir = snapshots_dir / "main"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = snapshot_dir / model_name
    temp_path = snapshot_dir / f"{model_name}.download"
    
    print(f"📁 HuggingFace 缓存目录: {cache_dir}")
    print(f"📁 模型将保存到: {output_path}")
    
    # 如果已存在完整文件，询问是否覆盖
    if output_path.exists():
        file_size = output_path.stat().st_size
        if file_size > 80 * 1024 * 1024:  # 大于 80MB 认为是完整的
            print(f"✅ 模型文件已存在: {output_path}")
            print(f"📦 文件大小: {file_size / (1024*1024):.1f} MB")
            response = input("是否重新下载? (y/N): ").strip().lower()
            if response != 'y':
                print("跳过下载")
                return
            else:
                output_path.unlink()  # 删除旧文件
    
    # 检查是否有未完成的下载
    resume_pos = 0
    if temp_path.exists():
        resume_pos = temp_path.stat().st_size
        print(f"🔄 检测到未完成的下载，将从 {resume_pos / (1024*1024):.1f} MB 处继续")
    
    print(f"\n📥 开始下载模型: {model_name}")
    print(f"💾 保存位置: {output_path.absolute()}\n")
    
    # 尝试每个 URL
    for i, url in enumerate(urls):
        try:
            source = "国内镜像站" if "hf-mirror" in url else "HuggingFace 官方"
            print(f"尝试从 {source} 下载...")
            
            # 设置断点续传的请求头
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            # 发起请求
            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()
            
            # 获取文件总大小
            if resume_pos > 0 and response.status_code == 206:
                # 断点续传成功
                content_range = response.headers.get('content-range', '')
                if content_range:
                    total_size = int(content_range.split('/')[-1])
                else:
                    total_size = resume_pos + int(response.headers.get('content-length', 0))
                print(f"✅ 断点续传支持，从 {resume_pos / (1024*1024):.1f} MB 继续下载")
            else:
                # 全新下载
                total_size = int(response.headers.get('content-length', 0))
                resume_pos = 0
            
            # 使用 tqdm 显示进度条
            try:
                from tqdm import tqdm
                progress_bar = tqdm(
                    total=total_size, 
                    initial=resume_pos,
                    unit='B', 
                    unit_scale=True, 
                    desc=model_name
                )
            except ImportError:
                print("提示: 安装 tqdm 可显示进度条 (pip install tqdm)")
                progress_bar = None
            
            # 下载文件（先下载到临时文件）
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(temp_path, mode) as f:
                downloaded = resume_pos
                for chunk in response.iter_content(chunk_size=32768):  # 32KB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_bar:
                            progress_bar.update(len(chunk))
                        elif total_size > 0 and downloaded % (1024 * 1024 * 5) == 0:  # 每 5MB 显示一次
                            percent = (downloaded / total_size) * 100
                            print(f"\r进度: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.1f}%)", end='')
            
            if progress_bar:
                progress_bar.close()
            
            # 下载完成，重命名临时文件
            if temp_path.exists():
                temp_path.rename(output_path)
            
            print(f"\n✅ 下载完成！")
            print(f"📁 文件位置: {output_path.absolute()}")
            print(f"📦 文件大小: {output_path.stat().st_size / (1024*1024):.1f} MB")
            print(f"\n💡 模型已保存到 HuggingFace 缓存目录，FormulaExtractor 将自动识别")
            return
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 下载被中断")
            print(f"💾 已保存进度到: {temp_path}")
            print("💡 下次运行此脚本将自动继续下载")
            return
        except Exception as e:
            print(f"\n❌ 从 {source} 下载失败: {e}")
            if i < len(urls) - 1:
                print("尝试下一个源...\n")
                # 清理可能损坏的临时文件
                if temp_path.exists() and resume_pos == 0:
                    temp_path.unlink()
            else:
                print("\n所有下载源均失败，请检查网络或手动下载：")
                print(f"下载地址: https://huggingface.co/LouiseBloch/ArxivFormulaYOLOv8/tree/main")
                print(f"保存到: {output_path.absolute()}")
                if temp_path.exists():
                    print(f"\n部分下载已保存到: {temp_path}")
                    print("下次运行可继续下载")

if __name__ == "__main__":
    try:
        download_model()
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
