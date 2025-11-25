# 确保虚拟环境已激活
pip install --upgrade pip

# 安装所有依赖（这会需要一些时间）
pip install -r requirements.txt

# 下载spaCy英文模型
python -m spacy download en_core_web_sm

# 下载spaCy中文模型（如果需要处理中文文档）
python -m spacy download zh_core_web_sm

conda install -c conda-forge tesseract -y

conda install -c conda-forge pandoc -y

pip install python-docx

python examples\layer3_example.py

python run_web.py
http://127.0.0.1:5000