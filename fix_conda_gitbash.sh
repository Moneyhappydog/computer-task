#!/bin/bash
# ============================================
# Conda Git Bash 路径修复脚本
# 完全重新配置 conda 在 Git Bash 中的使用
# ============================================

echo "=========================================="
echo "开始修复 Conda Git Bash 配置"
echo "=========================================="

# 1. 备份现有配置文件
echo ""
echo "步骤 1: 备份现有配置文件..."
if [ -f ~/.bash_profile ]; then
    cp ~/.bash_profile ~/.bash_profile.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ 已备份 .bash_profile"
fi
if [ -f ~/.bashrc ]; then
    cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ 已备份 .bashrc"
fi

# 2. 检查 conda 安装路径
echo ""
echo "步骤 2: 检查 conda 安装路径..."
CONDA_PATH="/d/anaconda"
if [ ! -f "$CONDA_PATH/Scripts/conda.exe" ]; then
    echo "❌ 错误: 找不到 $CONDA_PATH/Scripts/conda.exe"
    echo "请确认 conda 安装路径，然后修改脚本中的 CONDA_PATH 变量"
    exit 1
fi
echo "✓ 找到 conda: $CONDA_PATH/Scripts/conda.exe"

# 3. 清理 .bash_profile 中的旧 conda 配置
echo ""
echo "步骤 3: 清理 .bash_profile 中的旧配置..."
if [ -f ~/.bash_profile ]; then
    # 移除所有包含 conda 的行（除了注释）
    sed -i '/conda/d' ~/.bash_profile
    # 移除所有包含 cygdrive 的行
    sed -i '/cygdrive/d' ~/.bash_profile
    echo "✓ 已清理 .bash_profile"
fi

# 4. 清理 .bashrc 中的旧 conda 配置
echo ""
echo "步骤 4: 清理 .bashrc 中的旧配置..."
if [ -f ~/.bashrc ]; then
    # 移除所有包含 conda 的别名和配置
    sed -i '/alias conda/d' ~/.bashrc
    sed -i '/conda initialize/d' ~/.bashrc
    sed -i '/__conda_setup/d' ~/.bashrc
    sed -i '/conda activate/d' ~/.bashrc
    echo "✓ 已清理 .bashrc"
fi

# 5. 添加正确的 conda 配置到 .bashrc
echo ""
echo "步骤 5: 添加正确的 conda 配置..."
cat >> ~/.bashrc << 'EOF'

# ============================================
# Conda 配置 (Git Bash)
# ============================================
# 使用别名方式，避免路径问题
alias conda='/d/anaconda/Scripts/conda.exe'
alias conda-activate='source /d/anaconda/etc/profile.d/conda.sh && conda activate'
alias conda-deactivate='conda deactivate'

# 初始化 conda（如果需要 base 环境自动激活）
# 取消下面这行的注释以启用 base 环境自动激活
# eval "$(/d/anaconda/Scripts/conda.exe shell.bash hook)"
EOF

echo "✓ 已添加 conda 配置到 .bashrc"

# 6. 验证配置
echo ""
echo "步骤 6: 验证配置..."
source ~/.bashrc

if conda --version > /dev/null 2>&1; then
    echo "✓ Conda 配置成功！"
    echo ""
    echo "当前 conda 版本:"
    conda --version
else
    echo "❌ Conda 配置失败，请检查路径"
    exit 1
fi

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  1. 重新打开 Git Bash，或运行: source ~/.bashrc"
echo "  2. 使用 conda 命令: conda --version"
echo "  3. 创建环境: conda create -n dita-converter python=3.10 -y"
echo "  4. 激活环境: conda activate dita-converter"
echo ""

