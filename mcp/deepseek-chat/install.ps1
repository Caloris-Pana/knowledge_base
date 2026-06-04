$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetDir = Join-Path $env:USERPROFILE ".config\opencode\skills\deepseek-chat"
$configFile = Join-Path $env:USERPROFILE ".config\opencode\opencode.jsonc"

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   DeepSeek Chat MCP + Skill 一键安装脚本                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create target directory
Write-Host "[1/4] 创建目标目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

# Step 2: Copy files
Write-Host "[2/4] 复制文件..." -ForegroundColor Yellow
Copy-Item -Path "$scriptDir\index.js" -Destination $targetDir -Force
Copy-Item -Path "$scriptDir\package.json" -Destination $targetDir -Force
Copy-Item -Path "$scriptDir\SKILL.md" -Destination $targetDir -Force
Copy-Item -Path "$scriptDir\setup-token.ps1" -Destination $targetDir -Force

# Step 3: Install npm dependencies
Write-Host "[3/4] 安装 Node.js 依赖..." -ForegroundColor Yellow
Push-Location $targetDir
npm install --production
if ($LASTEXITCODE -ne 0) {
  Write-Host "❌ npm install 失败，请确保已安装 Node.js" -ForegroundColor Red
  Pop-Location
  exit 1
}
Pop-Location

# Step 4: Update opencode.jsonc
Write-Host "[4/4] 更新 opencode 配置..." -ForegroundColor Yellow
$config = Get-Content $configFile -Raw -Encoding UTF8 | ConvertFrom-Json

if (-not $config.skills) {
  $config | Add-Member -Type NoteProperty -Name "skills" -Value @{ paths = @() }
}
if (-not $config.skills.paths) {
  $config.skills | Add-Member -Type NoteProperty -Name "paths" -Value @()
}
$targetPath = ".opencode/skills"
if ($targetPath -notin $config.skills.paths) {
  $config.skills.paths += $targetPath
}

if (-not $config.mcp) {
  $config | Add-Member -Type NoteProperty -Name "mcp" -Value @{}
}
if (-not $config.mcp."deepseek-chat") {
  $nodePath = (Get-Command node).Source
  $mcpEntry = @{
    type = "local"
    command = @($nodePath, "$targetDir\index.js")
    enabled = $true
  }
  $config.mcp | Add-Member -Type NoteProperty -Name "deepseek-chat" -Value $mcpEntry
}

$configJson = $config | ConvertTo-Json -Depth 10
Set-Content -Path $configFile -Value $configJson -Encoding UTF8

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "接下来请运行 setup-token.ps1 配置 DeepSeek 登录凭证：" -ForegroundColor Yellow
Write-Host "  & '$targetDir\setup-token.ps1'" -ForegroundColor White
Write-Host ""
Write-Host "配置完成后，重启 opencode 即可使用 ds_list_sessions 等命令。" -ForegroundColor Green
