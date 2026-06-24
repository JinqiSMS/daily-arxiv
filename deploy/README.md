# Daily arXiv 部署说明

本目录包含将 Daily arXiv 配置为 Linux 系统服务的脚本和配置文件。

## 📂 文件说明

- `daily-arxiv-scheduler.service`: 调度器服务的 systemd 配置文件，负责定时运行任务。
- `daily-arxiv-web.service`: Web 服务的 systemd 配置文件，负责提供网页界面。
- `start_with_exist_conda_env.sh`: **一键部署脚本**，自动注册服务并启动。
- `start.sh`: 交互式启动脚本（旧版），用于手动测试运行。

## 🚀 快速部署

前提：确保你已经创建了名为 `daily-arxiv` 的 Conda 环境，并且项目依赖已安装。

直接运行以下命令即可完成部署（开机自启 + 立即启动）：

```bash
bash deploy/start_with_exist_conda_env.sh
```

脚本会自动执行以下操作：
1. 将 `.service` 配置文件链接到系统目录。
2. 刷新 systemd 配置。
3. 设置服务开机自启。
4. 立即启动服务。

## 🛠️ 常用管理命令

部署完成后，你可以使用标准的 `systemctl` 命令来管理服务。

| 操作 | 调度器服务 (Scheduler) | Web 服务 (Web App) |
|------|----------------------|-------------------|
| **查看状态** | `sudo systemctl status daily-arxiv-scheduler` | `sudo systemctl status daily-arxiv-web` |
| **停止服务** | `sudo systemctl stop daily-arxiv-scheduler` | `sudo systemctl stop daily-arxiv-web` |
| **启动服务** | `sudo systemctl start daily-arxiv-scheduler` | `sudo systemctl start daily-arxiv-web` |
| **重启服务** | `sudo systemctl restart daily-arxiv-scheduler` | `sudo systemctl restart daily-arxiv-web` |
| **禁用自启** | `sudo systemctl disable daily-arxiv-scheduler` | `sudo systemctl disable daily-arxiv-web` |

## 📝 日志查看

服务运行日志会自动保存在项目根目录的 `logs/` 文件夹中。

- **调度器日志**: `logs/scheduler.log` (主要关注这个，查看每日任务执行情况)
- **Web 服务日志**: `logs/web.log` (Web 访问日志)
- **错误日志**: `logs/*.error.log`

实时查看日志命令：
```bash
# 查看调度器实时日志
tail -f logs/scheduler.log
```
