"""
完整测试脚本
测试四层文档处理流程
增强版：包含模型预加载、详细日志、超时控制
"""
import sys
import logging
from pathlib import Path
import json
import time
import os

os.environ['TRANSFORMERS_ATTN_IMPLEMENTATION'] = 'eager'

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 导入各层模块
try:
    from src.layer1_preprocessing.file_router import FileRouter
    from src.layer2_semantic.document_analyzer import DocumentAnalyzer
    from src.layer3_dita_conversion.converter import DITAConverter
    from src.layer4_quality_assurance.qa_manager import QAManager
    
    print("✅ 模块导入成功")
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_process.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def make_json_serializable(obj):
    """将对象转换为JSON可序列化的格式，保留真实数据"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_serializable(item) for item in obj)
    elif hasattr(obj, '__dict__'):
        try:
            return {k: make_json_serializable(v) for k, v in obj.__dict__.items() 
                   if not k.startswith('_') and not callable(v)}
        except:
            return str(obj)
    elif hasattr(obj, 'bbox'):
        return {
            'type': 'image',
            'x0': getattr(obj, 'x0', None),
            'y0': getattr(obj, 'y0', None), 
            'x1': getattr(obj, 'x1', None),
            'y1': getattr(obj, 'y1', None),
            'width': getattr(obj, 'width', None),
            'height': getattr(obj, 'height', None),
            'name': getattr(obj, 'name', None)
        }
    else:
        try:
            return str(obj)
        except:
            return f"<{obj.__class__.__name__}>"


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def diagnose_marker():
    """诊断 Marker 环境"""
    print_section("🔍 Marker 环境诊断")
    
    print("1️⃣ 测试 Marker 导入...")
    try:
        import marker
        print("   ✅ Marker 模块导入成功")
        print(f"   📦 Marker 版本: {getattr(marker, '__version__', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Marker 导入失败: {e}")
        return False
    
    print("\n2️⃣ 测试依赖库...")
    dependencies = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'pypdfium2': 'PyPDFium2',
        'PIL': 'Pillow',
        'ftfy': 'ftfy'
    }
    
    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {name} 已安装")
        except ImportError:
            print(f"   ❌ {name} 未安装")
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  缺少依赖，尝试安装:")
        print("   pip install marker-pdf[full]")
        return False
    
    print("\n3️⃣ 检查模型文件...")
    try:
        from marker.models import load_all_models
        print("   ⏳ 正在加载模型（首次运行会下载，可能需要几分钟）...")
        print("   💡 如果长时间无响应，请检查网络连接")
        
        start_time = time.time()
        models = load_all_models()
        load_time = time.time() - start_time
        
        print(f"   ✅ 模型加载成功 (耗时: {load_time:.2f}秒)")
        
        # 显示模型信息
        if isinstance(models, dict):
            print(f"   📊 加载的模型数量: {len(models)}")
            for key in models.keys():
                print(f"      - {key}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def preload_marker_models():
    """预加载 Marker 模型"""
    print_section("🔄 预加载 Marker 模型")
    
    try:
        from marker.models import load_all_models
        
        print("⏳ 正在加载 Marker 模型...")
        print("💡 提示:")
        print("   - 首次运行会自动下载模型文件（约1-2GB）")
        print("   - 下载时间取决于网络速度，可能需要10-30分钟")
        print("   - 后续运行会直接使用已下载的模型")
        print()
        
        start_time = time.time()
        models = load_all_models()
        load_time = time.time() - start_time
        
        print(f"✅ Marker 模型加载成功 (耗时: {load_time:.2f}秒)")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  模型加载被用户中断")
        return False
    except Exception as e:
        print(f"❌ Marker 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_layer1_preprocessing():
    """测试 Layer 1: 预处理"""
    
    print_section("📊 Layer 1: 文档预处理")
    
    input_file = project_root / "data" / "input" / "test.pdf"
    output_dir = project_root / "data" / "output" / "test_run" / "layer1"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        logger.error(f"❌ 输入文件不存在: {input_file}")
        return None
    
    logger.info(f"📄 输入文件: {input_file}")
    logger.info(f"📂 输出目录: {output_dir}")
    
    start_time = time.time()
    
    try:
        # 1. 文件路由和处理
        print("⏳ 步骤 1/2: 文件路由和处理...")
        
        print("   - 正在创建 FileRouter 实例...")
        file_router = FileRouter()
        print("   - FileRouter 创建成功")
        
        print("   - 正在处理 PDF 文件...")
        print("   💡 这个过程可能需要几分钟，取决于文件大小和复杂度")
        
        process_start = time.time()
        result = file_router.process_file(input_file)
        process_time = time.time() - process_start
        
        print(f"   - 文件处理完成 (耗时: {process_time:.2f}秒)")
        
        if not result.get('success', False):
            logger.error(f"❌ 文件处理失败: {result.get('error', 'Unknown error')}")
            return None
        
        file_type = result.get('file_type', 'unknown')
        logger.info(f"检测到文件类型: {file_type}")
        
        # 2. 结果整理
        print("⏳ 步骤 2/2: 结果整理...")
        
        layer1_time = time.time() - start_time
        
        print(f"\n✅ Layer 1 完成 (总耗时: {layer1_time:.2f}秒)")
        print(f"   - 文件类型: {file_type}")
        print(f"   - 提取的文本长度: {len(result.get('markdown', ''))}")
        
        # 保存结果
        output_file = output_dir / "layer1_result.json"
        serializable_result = make_json_serializable(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 结果已保存: {output_file}")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Layer 1 被用户中断")
        raise
    except Exception as e:
        logger.error(f"❌ Layer 1 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_layer2_semantic(layer1_result):
    """测试 Layer 2: 语义分析"""
    
    print_section("🧠 Layer 2: 语义分析")
    
    if not layer1_result:
        logger.error("❌ 缺少 Layer 1 结果")
        return None
    
    output_dir = project_root / "data" / "output" / "test_run" / "layer2"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # 1. 文档分析
        print("⏳ 步骤 1/1: 文档分析（包含语义分类）...")
        print("   - 正在创建 DocumentAnalyzer 实例...")
        analyzer = DocumentAnalyzer()
        
        print("   - 正在分析文档...")
        analysis_result = analyzer.analyze(
            markdown_content=layer1_result.get('markdown', ''),
            metadata=layer1_result.get('metadata', {})
        )
        
        layer2_time = time.time() - start_time
        
        result = {
            'analysis': analysis_result,
        }
        
        print(f"\n✅ Layer 2 完成 (耗时: {layer2_time:.2f}秒)")
        print(f"   - 语义块数量: {len(analysis_result.get('chunks', []))}")
        print(f"   - 类型分布: {analysis_result.get('statistics', {}).get('type_distribution', {})}")
        
        # 保存结果
        output_file = output_dir / "layer2_result.json"
        serializable_result = make_json_serializable(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 结果已保存: {output_file}")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Layer 2 被用户中断")
        raise
    except Exception as e:
        logger.error(f"❌ Layer 2 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_layer3_dita_conversion(layer2_result):
    """测试 Layer 3: DITA转换"""
    
    print_section("🔄 Layer 3: DITA结构化转换")
    
    if not layer2_result:
        logger.error("❌ 缺少 Layer 2 结果")
        return None
    
    output_dir = project_root / "data" / "output" / "test_run" / "layer3"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # 1. DITA转换
        print("⏳ 步骤 1/1: DITA结构化转换...")
        print("   - 正在创建 DITAConverter 实例...")
        converter = DITAConverter()
        
        # 获取语义分析结果
        analysis_result = layer2_result.get('analysis', {})
        chunks = analysis_result.get('chunks', [])
        
        if not chunks:
            logger.error("❌ 没有找到语义块，无法进行DITA转换")
            return None
        
        # 构建内容和标题
        content = '\n\n'.join([chunk.get('text', '') for chunk in chunks])
        title = chunks[0].get('title', 'Document') if chunks else 'Document'
        content_type = 'Concept'
        
        print("   - 正在执行 DITA 转换...")
        # 执行DITA转换
        dita_result = converter.convert(
            content=content,
            title=title,
            content_type=content_type,
            metadata=layer2_result.get('processing_metadata', {})
        )
        
        layer3_time = time.time() - start_time
        
        result = {
            'success': dita_result.get('success', False),
            'dita_xml': dita_result.get('dita_xml', ''),
            'content_type': dita_result.get('content_type', 'concept'),
            'title': dita_result.get('title', 'Document'),
            'structured_data': dita_result.get('structured_data', {}),
            'validation': dita_result.get('validation', {}),
            'errors': dita_result.get('errors', []),
            'warnings': dita_result.get('warnings', []),
            'metadata': dita_result.get('metadata', {})
        }
        
        print(f"\n✅ Layer 3 完成 (耗时: {layer3_time:.2f}秒)")
        print(f"   - 转换状态: {'成功' if result['success'] else '失败'}")
        print(f"   - 内容类型: {result['content_type']}")
        print(f"   - 标题: {result['title']}")
        dita_xml_length = len(result['dita_xml']) if result['dita_xml'] else 0
        print(f"   - DITA XML长度: {dita_xml_length}")
        
        # 如果转换失败，显示错误信息
        if not result['success']:
            print(f"   - 错误数量: {len(result.get('errors', []))}")
            print(f"   - 警告数量: {len(result.get('warnings', []))}")
            for i, error in enumerate(result.get('errors', [])[:3]):
                print(f"   - 错误 {i+1}: {error.get('message', 'Unknown error')}")
        
        # 保存结果
        output_file = output_dir / "layer3_result.json"
        serializable_result = make_json_serializable(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        # 保存DITA XML文件
        if result['dita_xml']:
            dita_file = output_dir / "output.dita"
            with open(dita_file, 'w', encoding='utf-8') as f:
                f.write(result['dita_xml'])
            print(f"   - DITA文件已保存: {dita_file}")
        else:
            print(f"   - ⚠️  DITA XML为空，未保存文件")
        
        logger.info(f"💾 结果已保存: {output_file}")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Layer 3 被用户中断")
        raise
    except Exception as e:
        logger.error(f"❌ Layer 3 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_layer4_quality_assurance(layer3_result):
    """测试 Layer 4: 质量保证"""
    
    print_section("✅ Layer 4: 质量保证和修复")
    
    if not layer3_result:
        logger.error("❌ 缺少 Layer 3 结果")
        return None
    
    output_dir = project_root / "data" / "output" / "test_run" / "layer4"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # 1. 质量检查和修复
        print("⏳ 步骤 1/1: 质量检查和智能修复...")
        print("   - 正在创建 QAManager 实例...")
        qa_manager = QAManager()
        
        # 获取DITA转换结果
        dita_xml = layer3_result.get('dita_xml', '')
        content_type = layer3_result.get('content_type', 'concept')
        
        if not dita_xml:
            logger.error("❌ 没有找到DITA XML，无法进行质量检查")
            return None
        
        print("   - 正在执行质量检查...")
        # 执行质量检查和修复
        qa_result = qa_manager.process(
            dita_xml=dita_xml,
            content_type=content_type,
            processing_metadata=layer3_result
        )
        
        layer4_time = time.time() - start_time
        
        result = {
            'success': qa_result.get('success', False),
            'final_dita_xml': qa_result.get('final_dita_xml', ''),
            'content_type': qa_result.get('content_type', 'concept'),
            'quality_report': qa_result.get('quality_report', {}),
            'step_results': qa_result.get('step_results', {}),
            'qa_metadata': qa_result.get('qa_metadata', {}),
            'quality_score': qa_result.get('quality_report', {}).get('quality_scores', {}).get('overall_quality', 0)
        }
        
        print(f"\n✅ Layer 4 完成 (耗时: {layer4_time:.2f}秒)")
        print(f"   - 质量评分: {result['quality_score']}/100")
        print(f"   - 处理状态: {'成功' if result['success'] else '失败'}")
        
        # 保存结果
        output_file = output_dir / "layer4_result.json"
        serializable_result = make_json_serializable(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        # 保存最终DITA文件
        if result['final_dita_xml']:
            final_file = output_dir / "final_dita.xml"
            with open(final_file, 'w', encoding='utf-8') as f:
                f.write(result['final_dita_xml'])
            print(f"   - 最终DITA文件已保存: {final_file}")
        
        # 保存质量报告
        if result['quality_report']:
            report_file = output_dir / "quality_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                serializable_report = make_json_serializable(result['quality_report'])
                json.dump(serializable_report, f, ensure_ascii=False, indent=2)
            print(f"   - 质量报告已保存: {report_file}")
        
        logger.info(f"💾 结果已保存: {output_file}")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Layer 4 被用户中断")
        raise
    except Exception as e:
        logger.error(f"❌ Layer 4 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_process():
    """完整测试流程"""
    
    print_section("🚀 开始完整测试")
    
    print(f"📍 项目根目录: {project_root}")
    print(f"📍 当前工作目录: {Path.cwd()}")
    
    total_start_time = time.time()
    
    # 预加载 Marker 模型
    print("\n" + "─"*80)
    if not preload_marker_models():
        print("❌ Marker 模型加载失败，无法继续测试")
        print("💡 建议:")
        print("   1. 检查网络连接")
        print("   2. 确保有足够的磁盘空间（至少2GB）")
        print("   3. 运行诊断: python -c \"from marker.models import load_all_models; load_all_models()\"")
        return False
    print("─"*80)
    
    # Layer 1: 预处理
    layer1_result = test_layer1_preprocessing()
    if not layer1_result:
        return False
    
    # Layer 2: 语义分析
    layer2_result = test_layer2_semantic(layer1_result)
    if not layer2_result:
        return False
    
    # Layer 3: DITA转换
    layer3_result = test_layer3_dita_conversion(layer2_result)
    if not layer3_result:
        return False
    
    # Layer 4: 质量保证
    layer4_result = test_layer4_quality_assurance(layer3_result)
    if not layer4_result:
        return False
    
    total_time = time.time() - total_start_time
    
    print_section("🎉 所有层级测试完成")
    print("✅ Layer 1: 文档预处理 - 完成")
    print("✅ Layer 2: 语义分析 - 完成") 
    print("✅ Layer 3: DITA结构化转换 - 完成")
    print("✅ Layer 4: 质量保证和修复 - 完成")
    print(f"\n⏱️  总耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
    
    # 生成完整报告
    final_output_dir = project_root / "data" / "output" / "test_run"
    final_output_dir.mkdir(parents=True, exist_ok=True)
    
    summary_report = {
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_time_seconds': round(total_time, 2),
        'total_time_minutes': round(total_time/60, 2),
        'layers': {
            'layer1': {
                'status': 'success' if layer1_result else 'failed',
                'output': 'layer1_result.json',
                'file_type': layer1_result.get('metadata', {}).get('file_type', 'unknown') if layer1_result else None,
                'text_length': len(layer1_result.get('markdown', '')) if layer1_result else 0
            },
            'layer2': {
                'status': 'success' if layer2_result else 'failed',
                'output': 'layer2_result.json',
                'chunks_count': len(layer2_result.get('analysis', {}).get('chunks', [])) if layer2_result else 0
            },
            'layer3': {
                'status': 'success' if layer3_result else 'failed',
                'output': 'layer3_result.json',
                'success': layer3_result.get('success', False) if layer3_result else False,
                'dita_xml_length': len(layer3_result.get('dita_xml') or '') if layer3_result else 0
            },
            'layer4': {
                'status': 'success' if layer4_result else 'failed',
                'output': 'layer4_result.json',
                'quality_score': layer4_result.get('quality_score', 0) if layer4_result else 0
            }
        }
    }
    
    # 保存完整报告
    summary_file = final_output_dir / "complete_test_report.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 完整测试报告已保存: {summary_file}")
    
    return True


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          📄 文档处理系统 - 完整测试脚本 (增强版)             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 首先运行诊断
        if not diagnose_marker():
            print("\n❌ Marker 环境诊断失败，建议先解决环境问题")
            print("\n💡 解决步骤:")
            print("   1. 重新安装 marker-pdf: pip install --upgrade marker-pdf")
            print("   2. 安装完整依赖: pip install marker-pdf[full]")
            print("   3. 检查网络连接（首次运行需要下载模型）")
            
            user_input = input("\n是否继续测试？(y/n): ").lower()
            if user_input != 'y':
                sys.exit(1)
        
        # 运行完整测试
        success = test_full_process()
        
        if success:
            print("\n" + "="*80)
            print("  🎉 测试成功完成！")
            print("="*80)
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("  ❌ 测试失败，请查看日志: test_process.log")
            print("="*80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)