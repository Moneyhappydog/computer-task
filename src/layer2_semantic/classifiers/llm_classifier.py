"""
LLM分类器 - Tier 2
使用Few-shot学习进行分类，处理边界案例
"""
from typing import Dict

# 导入工具模块
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.utils.ai_service import AIService

logger = setup_logger('llm_classifier')

class LLMClassifier:
    """基于LLM的Few-shot分类器 - Tier 2"""
    
    # Few-shot示例
    FEW_SHOT_EXAMPLES = """
## Classification Examples:

### Example 1: Task
**Title:** Installing Python
**Content:**
1. Go to python.org
2. Download the installer for your operating system
3. Run the installer
4. Check "Add Python to PATH"
5. Click Install
6. Verify installation by running `python --version`

**Type:** Task
**Reasoning:** Contains numbered procedural steps with imperative verbs (go, download, run, check, click). Clear action-oriented structure.

---

### Example 2: Concept
**Title:** What is Object-Oriented Programming?
**Content:**
Object-Oriented Programming (OOP) is a programming paradigm based on the concept of "objects". 
Objects contain data in the form of fields (attributes) and code in the form of procedures (methods).
OOP is characterized by four main principles: encapsulation, abstraction, inheritance, and polymorphism.
These principles enable developers to create modular, reusable, and maintainable code.

**Type:** Concept
**Reasoning:** Defines and explains a concept with descriptive statements. Contains definition pattern ("is a programming paradigm"). No procedural steps.

---

### Example 3: Reference
**Title:** API Parameters
**Content:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id   | int  | Yes      | Unique user identifier |
| name      | str  | No       | User display name |
| email     | str  | Yes      | User email address |
| role      | str  | No       | User role (admin/user) |

**Type:** Reference
**Reasoning:** Contains structured table with parameter specifications. Pure reference data, no explanations or steps.

---

### Example 4: Task
**Title:** Configuring the Database
**Content:**
To configure the database connection:
- Open the config.yaml file
- Set the database_url parameter to your database address
- Specify your username and password
- Save the file and restart the service

The configuration should look like this:
```yaml
database_url: postgresql://localhost:5432/mydb
username: admin
password: secret
```

**Type:** Task
**Reasoning:** Contains action-oriented steps (open, set, specify, save, restart) even though using bullet points. Includes code example as part of instructions.

---

### Example 5: Concept
**Title:** Understanding REST APIs
**Content:**
REST (Representational State Transfer) is an architectural style for building web services.
It relies on stateless, client-server communication using standard HTTP methods.
REST APIs use resources identified by URLs and support operations like GET, POST, PUT, and DELETE.

Key characteristics:
- Stateless: Each request contains all necessary information
- Client-Server: Separation of concerns
- Cacheable: Responses can be cached
- Uniform Interface: Consistent resource access

**Type:** Concept
**Reasoning:** Explains architectural concepts with descriptive statements. Lists characteristics (not action steps). No procedural instructions.

---

### Example 6: Reference
**Title:** HTTP Status Codes
**Content:**
**2xx Success:**
- 200 OK: Request succeeded
- 201 Created: Resource created
- 204 No Content: Success with no response body

**4xx Client Errors:**
- 400 Bad Request: Invalid syntax
- 401 Unauthorized: Authentication required
- 404 Not Found: Resource not found

**5xx Server Errors:**
- 500 Internal Server Error
- 503 Service Unavailable

**Type:** Reference
**Reasoning:** Lists reference information (status codes and meanings). Structured catalog format. No conceptual explanation or procedural steps.

"""

    def __init__(self, use_ai: bool = True):
        """初始化LLM分类器"""
        self.use_ai = use_ai
        if use_ai:
            self.ai_service = AIService()
            logger.info("✅ LLM Few-shot分类器已启用")
        else:
            logger.warning("⚠️ LLM分类器已禁用，将返回低置信度结果")

    def classify(self, chunk: Dict, features: Dict) -> Dict:
        """
        使用Few-shot LLM进行分类
        
        Args:
            chunk: 文本块
            features: 提取的特征
            
        Returns:
            分类结果:
            {
                "type": "Task|Concept|Reference",
                "confidence": 0.0-1.0,
                "scores": {"Task": 0.x, "Concept": 0.y, "Reference": 0.z},
                "reasoning": "Brief explanation"
            }
        """
        if not self.use_ai:
            return {
                "type": "Concept",
                "confidence": 0.3,
                "scores": {"Task": 0.33, "Concept": 0.34, "Reference": 0.33},
                "reasoning": "LLM disabled, returning low confidence default"
            }
        
        # 构建Few-shot prompt
        prompt = self._build_few_shot_prompt(chunk, features)
        
        try:
            # 调用LLM
            response = self.ai_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500,
                json_mode=True
            )
            
            # 解析响应
            result = self._parse_response(response)
            
            logger.info(
                f"  🤖 LLM分类: {result['type']} "
                f"(置信度: {result['confidence']:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM分类失败: {e}")
            return {
                "type": "Concept",
                "confidence": 0.3,
                "scores": {"Task": 0.33, "Concept": 0.34, "Reference": 0.33},
                "reasoning": f"Error: {str(e)}"
            }

    def _build_few_shot_prompt(self, chunk: Dict, features: Dict) -> str:
        """构建Few-shot提示词"""
        
        # 提取关键特征作为上下文
        feature_summary = f"""
Key Features Detected:
- Imperative verbs: {features.get('imperative_verbs', 0)}
- Action verbs: {features.get('action_verbs', 0)}
- Has numbered list: {features.get('has_numbered_list', False)}
- Has bullet list: {features.get('has_bullet_list', False)}
- Has table: {features.get('has_table', False)}
- Has definition pattern: {features.get('has_definition', False)}
- "Is" statements: {features.get('is_statements', 0)}
- Word count: {features.get('word_count', 0)}
- Code blocks: {features.get('code_blocks', 0)}
"""

        prompt = f"""You are a DITA content classifier. Classify the following content as Task, Concept, or Reference.

{self.FEW_SHOT_EXAMPLES}

Now classify this content:

**Title:** {chunk['title']}

**Content:**
{chunk['content'][:1500]}

{feature_summary}

**Classification Guidelines:**
- Task: Procedural steps, how-to instructions, action-oriented (imperative verbs)
- Concept: Explanatory content, definitions, background information (descriptive)
- Reference: Lookup information, tables, lists of parameters/commands (structured data)

**Output Format (JSON only):**
{{
"type": "Task|Concept|Reference",
"confidence": 0.0-1.0,
"scores": {{
"Task": 0.0-1.0,
"Concept": 0.0-1.0,
"Reference": 0.0-1.0
}},
"reasoning": "Brief explanation (1-2 sentences)"
}}

Respond with ONLY the JSON object, no other text.
"""
        return prompt

    def _parse_response(self, response: str) -> Dict:
        """解析LLM响应"""
        import json
        import re
        
        # 提取JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        result = json.loads(json_match.group())
        
        # 验证必需字段
        required_fields = ['type', 'confidence', 'scores', 'reasoning']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing field: {field}")
        
        # 规范化类型名称
        result['type'] = result['type'].capitalize()
        
        # 验证类型
        if result['type'] not in ['Task', 'Concept', 'Reference']:
            logger.warning(f"⚠️ 无效类型 {result['type']}，默认为Concept")
            result['type'] = 'Concept'
        
        # 确保置信度在 0-1 范围内
        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
        
        return result
