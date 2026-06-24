"""
Daily arXiv Agent - 主程序入口

每日追踪 arXiv 最新论文，使用 LLM 进行总结和分析
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils import load_config, load_env, setup_logging, get_date_string


def main(config_path: str = None):
    """主函数"""
    # 加载配置
    load_env()
    config = load_config(config_path)
    logger = setup_logging(config)
    
    logger.info("=" * 60)
    logger.info("Daily arXiv Agent 启动")
    logger.info(f"日期: {get_date_string()}")
    logger.info("=" * 60)
    
    try:
        # 第二步 - 实现论文爬取 ✅
        logger.info("步骤 1: 爬取 arXiv 论文...")
        from src.crawler.arxiv_fetcher import ArxivFetcher
        fetcher = ArxivFetcher(config)
        
        # 尝试获取论文，如果没找到，逐步放宽条件
        papers = fetcher.fetch_papers(days_back=2)
        
        if not papers:
            logger.warning("⚠️  过去2天没有找到符合条件的论文，尝试扩大到7天...")
            papers = fetcher.fetch_papers(days_back=7)
        
        if papers:
            fetcher.print_paper_summary(papers)
        else:
            logger.warning("⚠️  没有找到符合条件的论文")
            logger.info("💡 提示: 可以尝试以下方法：")
            logger.info("   1. 在 config.yaml 中增加 days_back 或 max_results")
            logger.info("   2. 减少或删除关键词过滤（设置 keywords: []）")
            logger.info("   3. 修改类别范围")
            return
        
        # 第三步 - 实现论文总结 ✅
        logger.info("\n步骤 2: 总结论文...")
        from src.summarizer.paper_summarizer import PaperSummarizer
        
        try:
            summarizer = PaperSummarizer(config)
            summarized_papers = summarizer.summarize_papers(papers)
            
            # 生成每日报告
            logger.info("\n生成每日报告...")
            report = summarizer.generate_daily_report(summarized_papers)
            
            # 保存报告
            report_path = f"data/summaries/report_{get_date_string()}.md"
            from pathlib import Path
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📄 每日报告已保存到: {report_path}")
            
        except Exception as e:
            logger.error(f"论文总结失败: {str(e)}")
            logger.info("继续执行后续步骤...")
            summarized_papers = papers
        
        # 第四步 - 实现趋势分析 ✅
        logger.info("\n步骤 3: 分析研究趋势...")
        try:
            from src.analyzer.trend_analyzer import TrendAnalyzer
            from src.summarizer.llm_factory import LLMClientFactory
            
            # 创建 LLM 客户端（用于深度分析）
            llm_client = LLMClientFactory.create_client(config)
            
            # 加载论文总结
            from src.utils import load_json
            summaries_data = load_json('data/summaries/latest.json')
            summaries = summaries_data.get('summaries', []) if summaries_data else []
            
            # 创建趋势分析器
            analyzer = TrendAnalyzer(config, llm_client)
            analysis = analyzer.analyze(papers, summaries)
            
            if analysis:
                analyzer.print_analysis_summary(analysis)
            
        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}", exc_info=True)
            logger.info("继续执行后续步骤...")
        
        logger.info("=" * 60)
        logger.info("✅ 所有任务完成！")
        logger.info("=" * 60)
        logger.info("提示: 运行 'python src/web/app.py' 启动 Web 服务查看结果")
        
    except Exception as e:
        logger.error(f"❌ 执行出错: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Daily arXiv Agent")
    parser.add_argument('--config', type=str, default=os.environ.get('DAILY_ARXIV_CONFIG', 'config/config.yaml'),
                        help='Path to the configuration file')
    args = parser.parse_args()
    
    main(args.config)
