$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$tokenFile = Join-Path $scriptDir "token.txt"

function PrintGuide {
  Clear-Host
  Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
  Write-Host "║           DeepSeek JWT Token 配置工具                       ║" -ForegroundColor Cyan
  Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
  Write-Host ""
  Write-Host "获取 Token（推荐方法）：" -ForegroundColor Yellow
  Write-Host "  1. 用浏览器打开 https://chat.deepseek.com 并登录你的账号" -ForegroundColor White
  Write-Host "  2. 按 F12 打开开发者工具，切换到 Console（控制台）" -ForegroundColor White
  Write-Host "  3. 粘贴以下命令并回车：" -ForegroundColor White
  Write-Host "    console.log(JSON.parse(localStorage.getItem('userToken')))" -ForegroundColor Cyan
  Write-Host "  4. 复制输出的 Token 值（完整值）" -ForegroundColor White
  Write-Host ""
  Write-Host "备用方法——通过 Application 面板：" -ForegroundColor DarkGray
  Write-Host "  在 Application → Local Storage → https://chat.deepseek.com 找到 userToken" -ForegroundColor DarkGray
  Write-Host ""
}

function Test-Token {
  param([string]$Token)
  $headers = @{
    Authorization = "Bearer $Token"
    "Content-Type" = "application/json"
    "X-Client-Version" = "1.0.0-always"
    "X-Client-Platform" = "web"
    "X-Client-Locale" = "en_US"
    Origin = "https://chat.deepseek.com"
    Referer = "https://chat.deepseek.com/"
  }
  try {
    $resp = Invoke-RestMethod -Uri "https://chat.deepseek.com/api/v0/chat_session/fetch_page" `
                              -Headers $headers -Method Get -ErrorAction Stop
    if ($resp.data.biz_data.chat_sessions) {
      return $true
    }
    return $false
  } catch {
    return $false
  }
}

PrintGuide

$token = Read-Host "请输入 Token"

if ([string]::IsNullOrWhiteSpace($token)) {
  Write-Host ""
  Write-Host "❌ Token 不能为空，操作已取消" -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "正在校验 Token 有效性..." -ForegroundColor Gray

if (Test-Token -Token $token) {
  Set-Content -Path $tokenFile -Value $token -NoNewline
  Write-Host "✅ 校验通过，Token 已保存到：" -ForegroundColor Green
  Write-Host "   $tokenFile" -ForegroundColor Green
  Write-Host ""
  Write-Host "现在可以正常使用 DeepSeek 对话查询功能了。" -ForegroundColor Green
} else {
  Write-Host ""
  Write-Host "❌ Token 无效，请确认已正确复制 userToken 的值。" -ForegroundColor Red
  Write-Host ""
  Write-Host "可能的原因：" -ForegroundColor Yellow
  Write-Host "  · Token 已过期，请刷新 https://chat.deepseek.com 页面后重试" -ForegroundColor White
  Write-Host "  · 复制时包含了多余的空格或换行" -ForegroundColor White
  Write-Host "  · 未登录 DeepSeek 账号" -ForegroundColor White
  exit 1
}
