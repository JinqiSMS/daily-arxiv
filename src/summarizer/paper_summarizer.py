"""
论文总结器

使用 LLM 对 arXiv 论文进行智能总结
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from src.utils import save_json, get_date_string, get_data_path, with_retry
from .llm_factory import LLMClientFactory


class PaperSummarizer:
    """论文总结器"""
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的学术论文分析助手。你的任务是阅读 arXiv 论文的标题和摘要，
然后生成一个简洁、准确的中文总结。

总结要求：
1. 用 2-3 句话概括论文的核心内容
2. 突出论文的主要创新点和贡献
3. 使用专业但易懂的语言
4. 保持客观和准确
5. 字数控制在 150-200 字以内
"""
    
    # 用户提示词模板
    USER_PROMPT_TEMPLATE = """请总结以下论文：

标题：{title}

作者：{authors}

摘要：
{abstract}

请用中文给出简洁的总结（150-200字）："""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger('daily_arxiv.summarizer')
        
        # 创建 LLM 客户端
        try:
            self.llm_client = LLMClientFactory.create_client(config)
            self.logger.info(f"使用 LLM: {self.llm_client.get_provider_name()}")
        except Exception as e:
            self.logger.error(f"初始化 LLM 客户端失败: {str(e)}")
            raise
    
    @with_retry(max_retries=3, initial_delay=3)
    def summarize_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """总结单篇论文
        
        Args:
            paper: 论文信息字典
            
        Returns:
            包含总结的论文信息
        """
        try:
            # 构建提示词
            authors_str = ", ".join(paper['authors'][:5])
            if len(paper['authors']) > 5:
                authors_str += " et al."
            
            prompt = self.USER_PROMPT_TEMPLATE.format(
                title=paper['title'],
                authors=authors_str,
                abstract=paper['abstract']
            )
            
            # 生成总结
            summary = self.llm_client.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            # 添加总结到论文信息
            paper_with_summary = paper.copy()
            paper_with_summary['summary'] = summary
            paper_with_summary['summarized_at'] = datetime.now().isoformat()
            
            return paper_with_summary
            
        except Exception as e:
            self.logger.error(f"总结论文失败 [{paper.get('title', 'Unknown')}]: {str(e)}")
            paper_with_summary = paper.copy()
            paper_with_summary['summary'] = f"总结生成失败: {str(e)}"
            paper_with_summary['summary_error'] = True
            return paper_with_summary
    
    def summarize_papers(self, papers: List[Dict[str, Any]], 
                        show_progress: bool = True) -> List[Dict[str, Any]]:
        """批量总结论文
        
        Args:
            papers: 论文列表
            show_progress: 是否显示进度条
            
        Returns:
            包含总结的论文列表
        """
        if not papers:
            self.logger.warning("没有论文需要总结")
            return []
        
        self.logger.info("=" * 60)
        self.logger.info(f"开始总结 {len(papers)} 篇论文")
        self.logger.info(f"使用模型: {self.llm_client.model}")
        self.logger.info("=" * 60)
        
        summarized_papers = []
        
        # 使用进度条
        iterator = tqdm(papers, desc="总结论文") if show_progress else papers
        
        for i, paper in enumerate(iterator, 1):
            try:
                self.logger.info(f"\n[{i}/{len(papers)}] 正在总结: {paper['title'][:50]}...")
                
                summarized_paper = self.summarize_paper(paper)
                summarized_papers.append(summarized_paper)
                
                if not summarized_paper.get('summary_error'):
                    self.logger.info(f"✓ 总结完成")
                    if not show_progress:
                        # 如果没有进度条，显示总结预览
                        summary_preview = summarized_paper['summary'][:100]
                        self.logger.info(f"  总结预览: {summary_preview}...")
                else:
                    self.logger.warning(f"⚠ 总结失败")
                    
            except Exception as e:
                self.logger.error(f"处理论文时出错: {str(e)}")
                paper_with_error = paper.copy()
                paper_with_error['summary'] = f"处理失败: {str(e)}"
                paper_with_error['summary_error'] = True
                summarized_papers.append(paper_with_error)
        
        # 统计
        success_count = sum(1 for p in summarized_papers if not p.get('summary_error'))
        fail_count = len(summarized_papers) - success_count
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"✅ 总结完成: {success_count} 篇成功, {fail_count} 篇失败")
        self.logger.info("=" * 60)
        
        # 保存结果
        self._save_summaries(summarized_papers)
        
        return summarized_papers
    
    def _save_summaries(self, papers: List[Dict[str, Any]]):
        """保存总结结果
        
        Args:
            papers: 包含总结的论文列表
        """
        if not papers:
            return
        
        # 获取存储路径
        data_path = get_data_path(self.config, 'summaries')
        Path(data_path).mkdir(parents=True, exist_ok=True)
        
        # 按日期保存
        date_str = get_date_string()
        filepath = f"{data_path}/summaries_{date_str}.json"
        
        # 保存数据
        save_json(papers, filepath)
        self.logger.info(f"💾 总结数据已保存到: {filepath}")
        
        # 同时保存一份到 latest.json
        latest_filepath = f"{data_path}/latest.json"
        save_json({
            'date': date_str,
            'count': len(papers),
            'papers': papers,
            'llm_provider': self.llm_client.get_provider_name(),
            'llm_model': self.llm_client.model,
        }, latest_filepath)
        self.logger.info(f"💾 最新总结已保存到: {latest_filepath}")
    
    def generate_daily_report(self, papers: List[Dict[str, Any]]) -> str:
        """生成每日报告
        
        Args:
            papers: 包含总结的论文列表
            
        Returns:
            报告文本
        """
        if not papers:
            return "今日没有论文。"
        
        report_parts = []
        report_parts.append(f"# 📚 每日 arXiv 论文总结")
        report_parts.append(f"\n**日期**: {get_date_string()}")
        report_parts.append(f"**论文数量**: {len(papers)} 篇")
        report_parts.append(f"**LLM**: {self.llm_client.get_provider_name()} ({self.llm_client.model})")
        report_parts.append("\n---\n")
        
        for i, paper in enumerate(papers, 1):
            report_parts.append(f"\n## {i}. {paper['title']}")
            report_parts.append(f"\n**作者**: {', '.join(paper['authors'][:3])}" + 
                              (" et al." if len(paper['authors']) > 3 else ""))
            report_parts.append(f"\n**类别**: {', '.join(paper['categories'][:3])}")
            report_parts.append(f"\n**链接**: [{paper['id']}]({paper['pdf_url']})")
            
            if 'summary' in paper and not paper.get('summary_error'):
                report_parts.append(f"\n**总结**:\n{paper['summary']}")
            else:
                report_parts.append(f"\n**总结**: 暂无")
            
            report_parts.append(f"\n**原文摘要**:\n{paper.get('abstract', '无摘要')}")
            
            report_parts.append("\n---\n")
        
        return "\n".join(report_parts)


def main():
    """测试函数"""
    from src.utils import load_config, load_env, setup_logging, load_json
    
    load_env()
    config = load_config()
    logger = setup_logging(config)
    
    # 加载已爬取的论文
    data_path = get_data_path(config, 'papers')
    latest_file = f"{data_path}/latest.json"
    data = load_json(latest_file)
    
    if not data or not data.get('papers'):
        logger.error("没有找到论文数据，请先运行论文爬取")
        return
    
    papers = data['papers'][:3]  # 只测试前3篇
    
    # 创建总结器
    summarizer = PaperSummarizer(config)
    
    # 总结论文
    summarized_papers = summarizer.summarize_papers(papers)
    
    # 生成报告
    report = summarizer.generate_daily_report(summarized_papers)
    print("\n" + report)


if __name__ == "__main__":
    main()
