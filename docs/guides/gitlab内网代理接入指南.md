# GitLab 内网代理接入指南（Windows 新员工版）

> 目标读者：**刚入职、需要访问公司内网 GitLab（`gitlab.irootech.com`）的 Windows 同学**。
> 你不需要懂 SSH 原理，**照着每一步复制粘贴即可**。全程约 15 分钟。
> 遇到问题直接跳到文末「常见问题 FAQ」。

---

## 一、这是在干什么？（30 秒看懂）

公司内网的 GitLab **不能从你的电脑直接访问**，但有一台**跳板机 `h20`** 可以访问它。
我们要做的，就是在你电脑和 `h20` 之间打一条**加密隧道**，让你的电脑"借道" `h20` 去访问内网：

```
你的电脑  ──加密隧道──►  跳板机 h20  ──►  内网 GitLab / 其他内网服务
```

打通后你会得到两个本地入口：

| 本地地址 | 作用 |
|----------|------|
| `127.0.0.1:8080` | 专门访问内网 GitLab（`gitlab.irootech.com`） |
| `127.0.0.1:1080` | 通用 SOCKS5 代理，访问**任意**内网地址（浏览器、git、curl 都能用） |

并且我们会把它设成**开机登录后自动运行、断线自动重连**，一次配好，以后不用管。

---

## 二、开始之前你需要准备

1. **一台 Windows 10/11 电脑**（自带 OpenSSH，无需额外安装）。
2. **跳板机 `h20` 的登录账号**：向运维/管理员申请，你会得到：
   - 跳板机地址（IP，例如 `10.147.254.3`）
   - 你的**用户名**（通常是你的域账号，如 `first.last`）
3. 建议全程使用 **PowerShell**（在开始菜单搜索 "PowerShell" 打开即可）。

> 💡 本指南所有命令都在 **PowerShell** 里执行，直接复制粘贴回车即可。

---

## 三、第一步：确认 SSH 客户端可用

在 PowerShell 里执行：

```powershell
ssh -V
```

**期望结果**：看到类似 `OpenSSH_for_Windows_9.5p2 ...` 的版本号，说明已就绪。

> ❌ 如果提示"不是内部或外部命令"：打开「设置 → 系统 → 可选功能」，添加 **"OpenSSH 客户端"** 后重开 PowerShell。

---

## 四、第二步：生成你的 SSH 密钥（如果还没有）

执行下面命令检查是否已有密钥：

```powershell
Test-Path "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

- 返回 `True` → 已有密钥，**跳到第五步**。
- 返回 `False` → 执行下面命令生成（一路回车，**不用设密码**）：

```powershell
ssh-keygen -t ed25519 -C "你的邮箱或姓名"
```

生成后，查看你的**公钥内容**（这串要交给管理员）：

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

> 📮 把上面输出的**整行公钥**发给运维/管理员，请他们添加到 `h20` 服务器上（放进 `h20` 上你账号的 `~/.ssh/authorized_keys`）。
> 这样你之后连接就**不用输密码**了。

---

## 五、第三步：配置 h20 主机别名

我们把跳板机信息写进 SSH 配置文件，之后只用敲 `h20` 就能连。

用记事本打开配置文件（不存在会自动新建）：

```powershell
notepad "$env:USERPROFILE\.ssh\config"
```

在文件**末尾**追加以下内容（**把 `HostName` 和 `User` 换成管理员给你的真实值**）：

```
Host h20
    HostName 10.147.254.3
    User first.last
```

保存关闭。

> ⚠️ `User` 一定要改成**你自己的用户名**，不要照抄示例里的 `first.last`。

---

## 六、第四步：测试能否免密登录

```powershell
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 h20 "echo SSH_OK; hostname"
```

**期望结果**：输出里出现 `SSH_OK` 和一串远端主机名，说明**免密登录成功**。

> ❌ 如果卡住或提示 `Permission denied`：说明公钥还没被添加到 `h20`，回到第二步联系管理员确认。
> （出现一行 `close - IO is still pending...` 是 Windows 的正常提示，可忽略。）

---

## 七、第五步：创建隧道守护脚本

这个脚本负责建立隧道，并且**断线后自动重连**。执行下面命令**一键生成**脚本文件（整段复制粘贴回车）：

```powershell
@'
$ErrorActionPreference = 'Continue'
$logFile = Join-Path $env:USERPROFILE '.ssh\ssh-tunnel-h20.log'
function Write-Log([string]$msg) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$ts  $msg" | Out-File -FilePath $logFile -Append -Encoding utf8
}
Write-Log "=== tunnel daemon started (PID $PID) ==="
while ($true) {
    Write-Log "connecting to h20 ..."
    & ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=10 -o TCPKeepAlive=yes -N -L 127.0.0.1:8080:gitlab.irootech.com:80 -D 127.0.0.1:1080 h20
    Write-Log "ssh exited (code $LASTEXITCODE), retry in 60s"
    Start-Sleep -Seconds 60
}
'@ | Set-Content -Path "$env:USERPROFILE\.ssh\ssh-tunnel-h20.ps1" -Encoding utf8
```

> 📌 上面用的是**单引号 here-string（`@'...'@`）**，里面的 `$PID`、`$env:...` 等变量会**原样写进脚本文件**、运行时才展开，这正是我们想要的。请**整段一起复制**，不要漏掉开头的 `@'` 和结尾单独一行的 `'@`。

**确认生成成功**：

```powershell
Test-Path "$env:USERPROFILE\.ssh\ssh-tunnel-h20.ps1"
```

返回 `True` 即可。

> 📖 脚本做了什么？用**一条 SSH 连接**同时开通 `8080`（GitLab）和 `1080`（SOCKS5 代理），断开就等 60 秒重连，并把日志写到 `.ssh\ssh-tunnel-h20.log`。

---

## 八、第六步：设置开机登录后自动运行

我们放一个"启动入口"到 Windows 的 **Startup（启动）文件夹**，登录时自动、**隐藏窗口**地拉起隧道。**无需管理员权限**。

一键生成启动入口（整段复制粘贴回车）：

```powershell
$startup = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start-ssh-tunnel-h20.vbs"
@'
Set sh = CreateObject("WScript.Shell")
p = sh.ExpandEnvironmentStrings("%USERPROFILE%") & "\.ssh\ssh-tunnel-h20.ps1"
sh.Run "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File " & Chr(34) & p & Chr(34), 0, False
'@ | Set-Content -Path $startup -Encoding ascii
Test-Path $startup
```

返回 `True` 即表示自启入口已就位。以后**每次登录电脑，隧道都会自动在后台启动**。

---

## 九、第七步：立即启动并验证

不用重启，现在就手动拉起一次：

```powershell
wscript.exe "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start-ssh-tunnel-h20.vbs"
```

等约 8 秒，检查两个端口是否都在监听：

```powershell
Start-Sleep -Seconds 8
Get-NetTCPConnection -State Listen -LocalPort 8080,1080 | Select-Object LocalPort,OwningProcess
```

**期望结果**：看到 `8080` 和 `1080` 两行，且 `OwningProcess`（进程号）**相同** —— 说明一条连接同时扛起了两个转发，隧道已生效 ✅

---

## 十、第八步：怎么用这条代理

### 方式 A：访问内网 GitLab（走 8080）

在浏览器地址栏直接打开：

```
http://127.0.0.1:8080
```

> 如果 GitLab 要求用域名访问，可让管理员协助把 `gitlab.irootech.com` 指向 `127.0.0.1`（修改 hosts），再正常访问 `http://gitlab.irootech.com:8080`。

### 方式 B：让 git 走 SOCKS5 代理（走 1080）

```powershell
git config --global http.proxy socks5://127.0.0.1:1080
git config --global https.proxy socks5://127.0.0.1:1080
```

> 取消代理：`git config --global --unset http.proxy` 、`git config --global --unset https.proxy`

### 方式 C：浏览器/其他工具走 SOCKS5

在浏览器或系统代理设置里填：**SOCKS5 主机 `127.0.0.1`，端口 `1080`**，即可访问所有内网地址。

---

## 十一、日常管理速查

| 我想…… | 复制这条命令 |
|--------|--------------|
| 看隧道是否在跑 / 端口 | `Get-NetTCPConnection -State Listen -LocalPort 8080,1080` |
| 手动启动隧道 | `wscript.exe "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start-ssh-tunnel-h20.vbs"` |
| 停止隧道 | `Get-Process ssh \| Stop-Process -Force` |
| 查看运行日志（最近 20 行） | `Get-Content "$env:USERPROFILE\.ssh\ssh-tunnel-h20.log" -Tail 20` |
| 取消开机自启 | `Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start-ssh-tunnel-h20.vbs"` |

---

## 十二、常见问题 FAQ

**Q1：端口只出现 8080，没有 1080（或反过来）？**
说明可能有别的程序占用了其中一个端口。先停止 `Get-Process ssh | Stop-Process -Force`，用 `Get-NetTCPConnection -LocalPort 1080` 查是谁占用，关掉后重新启动隧道。

**Q2：访问 8080 浏览器报错 / 502 / 协议错误？**
只要 `8080` 端口在监听，隧道链路就是通的。GitLab 常强制 HTTPS，直连 80 端口可能返回异常响应，属正常现象。优先用**方式 A 的域名访问**或**方式 C 的 SOCKS 代理**。

**Q3：连接总是很快断开、日志里不停重连？**
多半是 `h20` 账号/公钥有问题。回到**第六步**确认 `ssh h20` 能免密登录成功。

**Q4：能不能注册成 Windows 计划任务（进程被杀也自动拉起）？**
可以，但**需要管理员权限**（`Register-ScheduledTask` 无权限会报 `0x80070005`）。普通员工用本指南的 Startup 方案即可，脚本自带断线重连，日常足够。需要更强保障请联系运维。

**Q5：为什么用一条 SSH 连接同时开两个端口，而不是开两条？**
省资源。`-L`（GitLab 专线）和 `-D`（通用 SOCKS 代理）可以共用同一条连接，少一次认证、少一个进程。

---

## 附：关键文件位置一览

| 文件 | 路径 | 作用 |
|------|------|------|
| SSH 配置 | `%USERPROFILE%\.ssh\config` | 定义 `h20` 主机别名 |
| 守护脚本 | `%USERPROFILE%\.ssh\ssh-tunnel-h20.ps1` | 建隧道 + 断线自愈 |
| 自启入口 | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\start-ssh-tunnel-h20.vbs` | 登录时隐藏启动 |
| 运行日志 | `%USERPROFILE%\.ssh\ssh-tunnel-h20.log` | 排查连接问题 |
