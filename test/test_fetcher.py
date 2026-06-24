#!/usr/bin/env python3
"""
测试 arXiv 论文爬取功能

这个脚本用于测试论文爬取模块是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config, load_env, setup_logging
from src.crawler.arxiv_fetcher import ArxivFetcher


def test_query_building():
    """测试查询构建"""
    print("\n" + "=" * 60)
    print("测试 1: 查询构建")
    print("=" * 60)
    
    load_env()
    config = load_config()
    
    fetcher = ArxivFetcher(config)
    query = fetcher.build_query()
    
    print(f"配置的类别: {fetcher.categories}")
    print(f"配置的关键词: {fetcher.keywords}")
    print(f"构建的查询: {query}")
    print("✅ 查询构建测试通过\n")


def test_fetch_papers():
    """测试论文获取"""
    print("\n" + "=" * 60)
    print("测试 2: 论文获取")
    print("=" * 60)
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    # 修改配置以获取少量论文进行测试
    config['arxiv']['max_results'] = 5
    
    fetcher = ArxivFetcher(config)
    
    try:
        papers = fetcher.fetch_papers(days_back=3)  # 获取过去3天的论文
        
        if papers:
            print(f"\n✅ 成功获取 {len(papers)} 篇论文")
            
            # 显示第一篇论文的详细信息
            print("\n" + "-" * 60)
            print("示例论文详情:")
            print("-" * 60)
            paper = papers[0]
            print(f"标题: {paper['title']}")
            print(f"作者: {', '.join(paper['authors'][:3])}")
            print(f"类别: {', '.join(paper['categories'])}")
            print(f"发布时间: {paper['published']}")
            print(f"PDF链接: {paper['pdf_url']}")
            print(f"摘要: {paper['abstract'][:200]}...")
            
            # 显示统计信息
            stats = fetcher.get_paper_stats(papers)
            print("\n" + "-" * 60)
            print("统计信息:")
            print("-" * 60)
            print(f"总论文数: {stats['total_papers']}")
            print(f"总作者数: {stats['total_authors']}")
            print(f"类别分布: {stats['category_distribution']}")
            
        else:
            print("⚠️  没有找到符合条件的论文")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_save_load():
    """测试数据保存和加载"""
    print("\n" + "=" * 60)
    print("测试 3: 数据保存和加载")
    print("=" * 60)
    
    load_env()
    config = load_config()
    
    from src.utils import load_json, get_data_path
    
    # 检查是否有保存的数据
    data_path = get_data_path(config, 'papers')
    latest_file = f"{data_path}/latest.json"
    
    data = load_json(latest_file)
    if data:
        print(f"✅ 成功加载数据: {latest_file}")
        print(f"   日期: {data.get('date')}")
        print(f"   论文数量: {data.get('count')}")
    else:
        print(f"⚠️  没有找到保存的数据: {latest_file}")
        print("   请先运行论文爬取测试")


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 arXiv 论文爬取模块测试")
    print("=" * 70)
    
    try:
        # 测试 1: 查询构建
        test_query_building()
        
        # 测试 2: 论文获取
        test_fetch_papers()
        
        # 测试 3: 数据保存和加载
        test_save_load()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试完成！")
        print("=" * 70)
        print("\n提示:")
        print("  - 查看保存的数据: ls -lh data/papers/")
        print("  - 查看日志文件: tail -f logs/daily_arxiv.log")
        print("  - 运行完整流程: python main.py")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
