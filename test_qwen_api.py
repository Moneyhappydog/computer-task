"""测试千问API连接"""
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

try:
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍DITA标准"}
        ]
    )
    
    print("✅ API连接成功！")
    print(f"模型回复: {response.choices[0].message.content}")
    print(f"使用tokens: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"❌ API连接失败: {e}")