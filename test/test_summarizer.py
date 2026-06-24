#!/usr/bin/env python3
"""
测试 LLM 总结功能

这个脚本用于测试不同 LLM 提供商的论文总结功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config, load_env, setup_logging, load_json, get_data_path
from src.summarizer.llm_factory import LLMClientFactory
from src.summarizer.paper_summarizer import PaperSummarizer


def test_llm_client():
    """测试 LLM 客户端创建"""
    print("\n" + "=" * 70)
    print("测试 1: LLM 客户端创建")
    print("=" * 70)
    
    load_env()
    config = load_config()
    
    provider = config['llm']['provider']
    print(f"配置的提供商: {provider}")
    print(f"支持的提供商: {', '.join(LLMClientFactory.list_providers())}")
    
    try:
        client = LLMClientFactory.create_client(config)
        print(f"✅ {provider.upper()} 客户端创建成功")
        print(f"   模型: {client.model}")
        print(f"   温度: {client.temperature}")
        print(f"   最大 tokens: {client.max_tokens}")
        return client
    except Exception as e:
        print(f"❌ 创建客户端失败: {str(e)}")
        print("\n💡 提示:")
        print(f"   1. 检查 .env 文件中是否设置了 {provider.upper()}_API_KEY")
        print(f"   2. 确认 config.yaml 中的 llm.provider 设置正确")
        print(f"   3. 如果使用 vLLM，确保服务正在运行")
        return None


def test_simple_generation(client):
    """测试简单文本生成"""
    print("\n" + "=" * 70)
    print("测试 2: 简单文本生成")
    print("=" * 70)
    
    if not client:
        print("⚠️ 跳过测试（客户端未创建）")
        return
    
    prompt = "请用一句话介绍什么是 arXiv。"
    print(f"提示词: {prompt}")
    print("\n生成中...")
    
    try:
        response = client.generate(prompt)
        print(f"\n✅ 生成成功:")
        print(f"   {response}")
        return True
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        return False


def test_paper_summarization():
    """测试论文总结"""
    print("\n" + "=" * 70)
    print("测试 3: 论文总结")
    print("=" * 70)
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    # 加载论文数据
    data_path = get_data_path(config, 'papers')
    latest_file = f"{data_path}/latest.json"
    data = load_json(latest_file)
    
    if not data or not data.get('papers'):
        print("❌ 没有找到论文数据")
        print("💡 请先运行: python main.py 或 python test_fetcher.py")
        return
    
    papers = data['papers'][:2]  # 只测试前2篇
    print(f"找到 {data.get('count')} 篇论文，测试前 2 篇\n")
    
    try:
        # 创建总结器
        summarizer = PaperSummarizer(config)
        
        # 总结论文
        summarized_papers = summarizer.summarize_papers(papers, show_progress=False)
        
        # 显示结果
        print("\n" + "-" * 70)
        print("总结结果:")
        print("-" * 70)
        
        for i, paper in enumerate(summarized_papers, 1):
            print(f"\n[{i}] {paper['title'][:60]}...")
            if not paper.get('summary_error'):
                print(f"总结: {paper['summary']}")
            else:
                print(f"⚠️ 总结失败: {paper.get('summary', 'Unknown error')}")
        
        print("\n✅ 论文总结测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_different_providers():
    """测试不同的 LLM 提供商"""
    print("\n" + "=" * 70)
    print("测试 4: 不同 LLM 提供商对比")
    print("=" * 70)
    
    load_env()
    config = load_config()
    
    test_prompt = "请用一句话解释什么是深度学习。"
    providers = LLMClientFactory.list_providers()
    
    print(f"测试提示词: {test_prompt}\n")
    
    results = {}
    
    for provider in providers:
        print(f"\n尝试 {provider.upper()}...")
        
        # 临时修改配置
        test_config = config.copy()
        test_config['llm'] = config['llm'].copy()
        test_config['llm']['provider'] = provider
        
        try:
            client = LLMClientFactory.create_client(test_config)
            response = client.generate(test_prompt)
            results[provider] = response
            print(f"✅ {provider}: {response[:100]}...")
        except Exception as e:
            results[provider] = f"Error: {str(e)}"
            print(f"❌ {provider}: {str(e)[:100]}...")
    
    print("\n" + "=" * 70)
    print("对比结果:")
    print("=" * 70)
    
    for provider, response in results.items():
        print(f"\n{provider.upper()}:")
        print(f"  {response}")
    
    success_count = sum(1 for r in results.values() if not r.startswith("Error:"))
    print(f"\n✅ {success_count}/{len(providers)} 个提供商可用")


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 LLM 论文总结功能测试")
    print("=" * 70)
    
    try:
        # 测试 1: 创建客户端
        client = test_llm_client()
        
        # 测试 2: 简单生成
        if client:
            generation_ok = test_simple_generation(client)
            
            if generation_ok:
                # 测试 3: 论文总结
                test_paper_summarization()
        
        # 测试 4: 对比不同提供商（可选）
        print("\n" + "=" * 70)
        choice = input("\n是否测试所有 LLM 提供商对比？(y/n): ")
        if choice.lower() == 'y':
            test_different_providers()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试完成！")
        print("=" * 70)
        print("\n提示:")
        print("  - 查看总结数据: ls -lh data/summaries/")
        print("  - 查看报告: cat data/summaries/report_*.md")
        print("  - 运行完整流程: python main.py")
        print()
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
