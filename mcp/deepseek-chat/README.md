# DeepSeek Chat MCP + Skill for opencode

通过 opencode 读取 DeepSeek 网页端对话记录的 MCP 服务及配套 Skill。

## 安装

```powershell
# 进入插件目录后执行
.\install.ps1
```

安装脚本会自动：
1. 复制文件到 `%USERPROFILE%\.config\opencode\skills\deepseek-chat\`
2. 安装 Node.js 依赖
3. 更新 `opencode.jsonc` 配置

## 配置 Token

首次使用需运行：

```powershell
.\setup-token.ps1
```

按提示操作：
1. 打开 https://chat.deepseek.com 并登录
2. F12 → Application → Local Storage → 复制 `userToken` 的值
3. 粘贴到脚本中

## Token 过期续期

当查询对话记录时返回 Token 过期提示，重新运行 `setup-token.ps1` 即可。

## 提供的工具

| 工具名 | 说明 |
|--------|------|
| `ds_list_sessions` | 查看对话总览或按月详情 |
| `ds_get_session` | 获取某条会话的完整消息 |
| `ds_get_session_by_title` | 按标题模糊搜索会话 |

## 目录结构

```
%USERPROFILE%\.config\opencode\skills\deepseek-chat\
├── index.js              MCP 服务端
├── package.json          Node.js 依赖
├── SKILL.md              Skill 指令
├── setup-token.ps1       Token 配置脚本
├── install.ps1           安装脚本
├── token.txt             存放 JWT（请勿分享）
└── README.md             本文件
```
