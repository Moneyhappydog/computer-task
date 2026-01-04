#!/bin/bash
# 一键修复 conda Git Bash 路径问题
# 直接在 Git Bash 中运行此脚本，或复制下面的命令执行

echo "开始修复 conda 配置..."

# 备份
cp ~/.bash_profile ~/.bash_profile.backup 2>/dev/null
cp ~/.bashrc ~/.bashrc.backup 2>/dev/null

# 清理旧配置
sed -i '/conda/d' ~/.bash_profile 2>/dev/null
sed -i '/cygdrive/d' ~/.bash_profile 2>/dev/null
sed -i '/alias conda/d' ~/.bashrc 2>/dev/null
sed -i '/conda initialize/d' ~/.bashrc 2>/dev/null
sed -i '/__conda_setup/d' ~/.bashrc 2>/dev/null

# 添加正确配置
cat >> ~/.bashrc << 'EOF'

# Conda 配置 - Git Bash 修复版
alias conda='/d/anaconda/Scripts/conda.exe'
EOF

# 重新加载
source ~/.bashrc

# 验证
echo ""
echo "验证 conda..."
if conda --version 2>/dev/null; then
    echo "✓ 修复成功！"
    conda --version
else
    echo "❌ 修复失败，请检查路径"
fi

