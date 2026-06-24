#!/usr/bin/env python3
"""
测试趋势分析功能

这个脚本用于测试趋势分析模块是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config, load_env, setup_logging, load_json
from src.analyzer.trend_analyzer import TrendAnalyzer
from src.summarizer.llm_factory import LLMClientFactory


def test_keyword_extraction():
    """测试关键词提取"""
    print("\n" + "=" * 60)
    print("测试 1: 关键词提取")
    print("=" * 60)
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    # 加载论文数据
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        print("❌ 未找到论文数据，请先运行: python main.py")
        return False
    
    papers = papers_data.get('papers', [])
    print(f"加载了 {len(papers)} 篇论文")
    
    # 创建分析器（不需要 LLM）
    analyzer = TrendAnalyzer(config, llm_client=None)
    
    # 提取关键词
    keywords = analyzer._extract_keywords(papers, top_n=20)
    
    print("\n✅ 关键词提取成功")
    print(f"提取了 {len(keywords)} 个关键词")
    print("\nTop 20 关键词:")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw['keyword']} (权重: {kw['score']:.4f})")
    
    return True


def test_topic_extraction():
    """测试主题提取"""
    print("\n" + "=" * 60)
    print("测试 2: 主题提取")
    print("=" * 60)
    
    load_env()
    config = load_config()
    
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        return False
    
    papers = papers_data.get('papers', [])
    
    analyzer = TrendAnalyzer(config, llm_client=None)
    
    # 提取主题
    topics = analyzer._extract_topics(papers, n_topics=5)
    
    print("\n✅ 主题提取成功")
    print(f"提取了 {len(topics)} 个主题")
    print("\n主题详情:")
    for topic in topics:
        print(f"\n主题 {topic['topic_id']}:")
        print(f"  关键词: {', '.join(topic['keywords'][:8])}")
    
    return True


def test_wordcloud_generation():
    """测试词云生成"""
    print("\n" + "=" * 60)
    print("测试 3: 词云生成")
    print("=" * 60)
    
    load_env()
    config = load_config()
    
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        return False
    
    papers = papers_data.get('papers', [])
    
    analyzer = TrendAnalyzer(config, llm_client=None)
    
    # 生成词云
    wordcloud_path = analyzer._generate_wordcloud(papers)
    
    print(f"\n✅ 词云生成成功")
    print(f"保存位置: {wordcloud_path}")
    
    import os
    if os.path.exists(wordcloud_path):
        size = os.path.getsize(wordcloud_path)
        print(f"文件大小: {size / 1024:.2f} KB")
        return True
    else:
        print("❌ 词云文件未找到")
        return False


def test_statistics():
    """测试统计分析"""
    print("\n" + "=" * 60)
    print("测试 4: 统计分析")
    print("=" * 60)
    
    load_env()
    config = load_config()
    
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        return False
    
    papers = papers_data.get('papers', [])
    
    # 尝试加载总结
    summaries_data = load_json('data/summaries/latest.json')
    summaries = summaries_data.get('summaries', []) if summaries_data else None
    
    analyzer = TrendAnalyzer(config, llm_client=None)
    
    # 生成统计
    statistics = analyzer._generate_statistics(papers, summaries)
    
    print("\n✅ 统计分析成功")
    print(f"\n统计结果:")
    print(f"  总论文数: {statistics['total_papers']}")
    print(f"  总作者数: {statistics['total_authors']}")
    print(f"  研究类别: {statistics['total_categories']}")
    
    print(f"\n类别分布 (Top 5):")
    for i, (cat, count) in enumerate(list(statistics['category_distribution'].items())[:5], 1):
        print(f"  {i}. {cat}: {count} 篇")
    
    print(f"\n高产作者:")
    for author, count in list(statistics['prolific_authors'].items())[:5]:
        print(f"  - {author}: {count} 篇")
    
    return True


def test_llm_analysis():
    """测试 LLM 深度分析"""
    print("\n" + "=" * 60)
    print("测试 5: LLM 深度分析")
    print("=" * 60)
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        return False
    
    papers = papers_data.get('papers', [])[:10]  # 只用前10篇测试
    print(f"使用 {len(papers)} 篇论文进行测试")
    
    # 尝试加载总结
    summaries_data = load_json('data/summaries/latest.json')
    summaries = summaries_data.get('summaries', [])[:10] if summaries_data else []
    
    try:
        # 创建 LLM 客户端
        llm_client = LLMClientFactory.create_client(config)
        
        analyzer = TrendAnalyzer(config, llm_client)
        
        # 提取关键词和主题
        keywords = analyzer._extract_keywords(papers, top_n=20)
        topics = analyzer._extract_topics(papers, n_topics=3)
        
        # 生成 LLM 分析
        print("\n正在调用 LLM 生成分析...")
        llm_analysis = analyzer._generate_llm_analysis(papers, summaries, keywords, topics)
        
        print("\n✅ LLM 分析成功")
        print("\n分析结果预览:")
        for key in ['hotspots', 'trends', 'future_directions', 'research_ideas']:
            content = llm_analysis.get(key, '')
            if content:
                preview = content[:150] + "..." if len(content) > 150 else content
                print(f"\n{key}: {preview}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ LLM 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_full_analysis():
    """测试完整分析流程"""
    print("\n" + "=" * 60)
    print("测试 6: 完整分析流程")
    print("=" * 60)
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    papers_data = load_json('data/papers/latest.json')
    if not papers_data:
        return False
    
    papers = papers_data.get('papers', [])
    
    # 加载总结
    summaries_data = load_json('data/summaries/latest.json')
    summaries = summaries_data.get('summaries', []) if summaries_data else []
    
    try:
        # 创建 LLM 客户端
        llm_client = LLMClientFactory.create_client(config)
        
        analyzer = TrendAnalyzer(config, llm_client)
        
        # 执行完整分析
        print(f"\n分析 {len(papers)} 篇论文...")
        analysis = analyzer.analyze(papers, summaries)
        
        if analysis:
            print("\n✅ 完整分析成功")
            analyzer.print_analysis_summary(analysis)
            
            print("\n生成的文件:")
            print(f"  - JSON: data/analysis/analysis_{analysis['date']}.json")
            print(f"  - Markdown: data/analysis/report_{analysis['date']}.md")
            print(f"  - 词云: {analysis['wordcloud_path']}")
            
            return True
        else:
            print("❌ 分析结果为空")
            return False
            
    except Exception as e:
        print(f"\n❌ 完整分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 趋势分析模块测试")
    print("=" * 70)
    
    results = {
        '关键词提取': False,
        '主题提取': False,
        '词云生成': False,
        '统计分析': False,
        'LLM 深度分析': False,
        '完整分析流程': False
    }
    
    try:
        # 基础测试（不需要 LLM）
        results['关键词提取'] = test_keyword_extraction()
        results['主题提取'] = test_topic_extraction()
        results['词云生成'] = test_wordcloud_generation()
        results['统计分析'] = test_statistics()
        
        # LLM 相关测试
        print("\n" + "=" * 60)
        print("是否测试 LLM 功能？(需要配置 API Key)")
        print("=" * 60)
        
        user_input = input("\n继续 LLM 测试? (y/n, 默认 n): ").strip().lower()
        
        if user_input == 'y':
            results['LLM 深度分析'] = test_llm_analysis()
            results['完整分析流程'] = test_full_analysis()
        else:
            print("\n跳过 LLM 测试")
        
        # 总结
        print("\n" + "=" * 70)
        print("📊 测试结果总结")
        print("=" * 70)
        
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "⏭️  跳过" if not passed and test_name in ['LLM 深度分析', '完整分析流程'] else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        passed_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print("\n" + "=" * 70)
        print(f"测试通过率: {passed_count}/{total_count}")
        print("=" * 70)
        
        print("\n💡 提示:")
        print("  - 查看生成的词云: data/analysis/wordcloud_*.png")
        print("  - 查看分析报告: data/analysis/report_*.md")
        print("  - 运行完整流程: python main.py")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
