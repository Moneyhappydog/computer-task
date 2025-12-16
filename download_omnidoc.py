from huggingface_hub import snapshot_download
import os

# 设置下载目录为绝对路径，确保准确
local_dir = os.path.join(os.getcwd(), "data", "input", "OmniDocBench")

print(f"开始下载 OmniDocBench 数据集到: {local_dir}")
print("这可能需要一些时间，取决于网络速度...")

try:
    snapshot_download(
        repo_id="opendatalab/OmniDocBench",
        repo_type="dataset",
        local_dir=local_dir,
        local_dir_use_symlinks=False,  # 下载真实文件，而不是链接
        resume_download=True,          # 支持断点续传
        max_workers=8                  # 并发下载数
    )
    print("下载完成！")
except Exception as e:
    print(f"下载出错: {e}")
