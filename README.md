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


python test_layer1.py --pdf uploads/5b946750-56f2-4e6e-82ac-5e02cfec5a72_First.pdf --word uploads/0048f9dc-258c-4fbb-ada0-7ca39a2a01fd_sample.docx 

conda install -c conda-forge poppler

conda activate venv ; python test_layer1.py --pdf "d:\codeC\VsCodeP\dita-converter\uploads\2023CVPR-CoMFormer.pdf"

conda activate venv; python test_layer2.py 

conda activate venv ; python test_integration.py "D:\codeC\VsCodeP\dita-converter\uploads\2023CVPR-CoMFormer.pdf" "D:\codeC\VsCodeP\dita-converter\uploads\0d98a7bb-bb4c-4d9b-800b-83da29355828_sample.docx"

