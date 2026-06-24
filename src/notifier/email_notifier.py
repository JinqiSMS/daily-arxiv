"""
邮件通知模块

发送任务执行结果通知
"""
import os
import smtplib
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import logging


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config):
        """
        初始化邮件通知器
        
        Args:
            config: 邮件配置字典
        """
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender = config.get('sender', '')
        self.password = os.getenv('EMAIL_PASSWORD', config.get('password', ''))
        self.recipients = config.get('recipients', [])
        self.on_success = config.get('on_success', True)
        self.on_failure = config.get('on_failure', True)
        
        self.logger = logging.getLogger(__name__)
    
    def send_notification(self, success=True, stats=None, error_msg=None, duration=0, report_content=None):
        """
        发送通知邮件
        
        Args:
            success: 任务是否成功
            stats: 统计信息字典
            error_msg: 错误信息
            duration: 执行耗时（秒）
            report_content: 报告内容（Markdown）
        
        Returns:
            bool: 是否发送成功
        """
        # 检查是否需要发送
        if success and not self.on_success:
            return True
        if not success and not self.on_failure:
            return True
        
        # 检查配置
        if not self.sender or not self.recipients:
            self.logger.warning("邮件发送者或收件人未配置，跳过邮件通知")
            return False
        
        if not self.password:
            self.logger.warning("邮件密码未配置，跳过邮件通知")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = self._get_subject(success)
            
            # 生成邮件内容
            html_content = self._generate_html_content(success, stats, error_msg, duration, report_content)
            text_content = self._generate_text_content(success, stats, error_msg, duration, report_content)
            
            # 添加内容
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件
            if self.smtp_port == 465:
                # 使用 SSL 连接 (Port 465)
                context = smtplib.ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=30) as server:
                    server.login(self.sender, self.password)
                    server.send_message(msg)
            else:
                # 使用 STARTTLS 连接 (Port 587 or 25)
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    if server.has_extn('STARTTLS'):
                        context = smtplib.ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()
                    server.login(self.sender, self.password)
                    server.send_message(msg)
            
            self.logger.info(f"邮件通知发送成功: {', '.join(self.recipients)}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}", exc_info=True)
            return False
    
    def _get_subject(self, success):
        """生成邮件主题"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        if success:
            return f"✅ Daily arXiv 任务成功 - {date_str}"
        else:
            return f"❌ Daily arXiv 任务失败 - {date_str}"
    
    def _generate_text_content(self, success, stats, error_msg, duration, report_content=None):
        """生成纯文本内容"""
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        content = []
        content.append("=" * 60)
        content.append("Daily arXiv 任务执行报告")
        content.append("=" * 60)
        content.append(f"执行时间: {date_str}")
        content.append(f"执行结果: {'✅ 成功' if success else '❌ 失败'}")
        content.append(f"执行耗时: {duration:.2f} 秒")
        content.append("")
        
        if success and stats:
            content.append("统计信息:")
            content.append("-" * 60)
            content.append(f"  论文数量: {stats.get('papers_count', 0)}")
            content.append(f"  总结数量: {stats.get('summaries_count', 0)}")
            content.append(f"  研究类别: {stats.get('categories_count', 0)}")
            content.append(f"  关键词数: {stats.get('keywords_count', 0)}")
            content.append("")
        
        if report_content:
            content.append("报告内容:")
            content.append("-" * 60)
            content.append(report_content)
            content.append("")
        
        if not success and error_msg:
            content.append("错误信息:")
            content.append("-" * 60)
            content.append(error_msg)
            content.append("")
        
        return '\n'.join(content)
    
    def _generate_html_content(self, success, stats, error_msg, duration, report_content=None):
        """生成 HTML 内容"""
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        status_color = '#28a745' if success else '#dc3545'
        status_icon = '✅' if success else '❌'
        status_text = '成功' if success else '失败'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .status {{
                    background: {status_color};
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 20px;
                    margin-bottom: 20px;
                }}
                .info {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .info-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #dee2e6;
                }}
                .info-item:last-child {{
                    border-bottom: none;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #666;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stat-value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .error {{
                    background: #f8d7da;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #dc3545;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #666;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    margin-top: 20px;
                }}
                /* Report styles */
                .report {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-top: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .markdown-body {{
                    font-size: 14px;
                    line-height: 1.6;
                }}
                .markdown-body h1, .markdown-body h2, .markdown-body h3 {{
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: 600;
                    line-height: 1.25;
                }}
                .markdown-body h2 {{
                    padding-bottom: .3em;
                    border-bottom: 1px solid #eaecef;
                }}
                .markdown-body p {{
                    margin-top: 0;
                    margin-bottom: 16px;
                }}
                .markdown-body code {{
                    padding: .2em .4em;
                    margin: 0;
                    font-size: 85%;
                    background-color: #f6f8fa;
                    border-radius: 6px;
                }}
                .markdown-body pre {{
                    padding: 16px;
                    overflow: auto;
                    font-size: 85%;
                    line-height: 1.45;
                    background-color: #f6f8fa;
                    border-radius: 6px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Daily arXiv 任务执行报告</h1>
            </div>
            
            <div class="status">
                {status_icon} 执行结果: {status_text}
            </div>
            
            <div class="info">
                <div class="info-item">
                    <span class="info-label">执行时间:</span> {date_str}
                </div>
                <div class="info-item">
                    <span class="info-label">执行耗时:</span> {duration:.2f} 秒
                </div>
            </div>
        """
        
        if success and stats:
            html += """
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{papers}</div>
                    <div class="stat-label">📄 论文数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summaries}</div>
                    <div class="stat-label">📝 总结数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{categories}</div>
                    <div class="stat-label">🏷️ 研究类别</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{keywords}</div>
                    <div class="stat-label">🔑 关键词数</div>
                </div>
            </div>
            """.format(
                papers=stats.get('papers_count', 0),
                summaries=stats.get('summaries_count', 0),
                categories=stats.get('categories_count', 0),
                keywords=stats.get('keywords_count', 0)
            )
        
        # Add report content
        if report_content:
            try:
                # Use extensions for better rendering (tables, fenced code blocks)
                report_body = markdown.markdown(report_content, extensions=['tables', 'fenced_code'])
                html += f"""
                <div class="report">
                    <h2 style="border-bottom: 2px solid #667eea; padding-bottom: 10px; color: #333;">📄 研究报告</h2>
                    <div class="markdown-body">
                        {report_body}
                    </div>
                </div>
                """
            except Exception as e:
                self.logger.warning(f"Markdown 转换失败: {e}")
                html += f"""
                <div class="report">
                    <h3>报告内容 (纯文本)</h3>
                    <pre style="white-space: pre-wrap;">{report_content}</pre>
                </div>
                """

        if not success and error_msg:
            html += f"""
            <div class="error">
                <strong>错误信息:</strong><br>
                {error_msg.replace(chr(10), '<br>')}
            </div>
            """
        
        html += """
            <div class="footer">
                <p style="margin-top: 20px; font-size: 12px;">
                    这是一封自动发送的邮件，请勿回复。
                </p>
            </div>
        </body>
        </html>
        """
        

        return html


def send_test_email(config):
    """发送测试邮件"""
    notifier = EmailNotifier(config)
    
    test_stats = {
        'papers_count': 20,
        'summaries_count': 20,
        'categories_count': 2,
        'keywords_count': 50
    }
    
    print("\n📧 发送测试邮件...")
    success = notifier.send_notification(
        success=True,
        stats=test_stats,
        duration=120.5
    )
    
    if success:
        print("✅ 测试邮件发送成功！")
    else:
        print("❌ 测试邮件发送失败！")
    
    return success
