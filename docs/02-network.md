# 02 · Windows 代理、WSL2 和下载问题

回到 [主教程](../README.md)。代理软件端口、Windows 版本和网络模式不同，不能只复制别人的 IP。

## 1. 先在 Windows 验证外网

PowerShell：

```powershell
curl.exe -I --connect-timeout 10 --max-time 30 https://github.com
Resolve-DnsName raw.githubusercontent.com -Type A
```

若 Windows 本身不通，先处理代理软件。浏览器插件能上网不代表 Git、Python 或 Docker 也在走代理。

## 2. Windows 11：镜像网络和自动代理

微软说明见 [WSL 网络](https://learn.microsoft.com/en-us/windows/wsl/networking)与 [配置文件](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)。这些能力需要受支持的系统和新版 WSL，不应假定 Windows 10 同样具备。

1. PowerShell 执行 `wsl --update`。
2. 执行 `notepad "$env:USERPROFILE\.wslconfig"`。
3. 参考本仓库 `config/wslconfig.example`，把条目合并进已有 `[wsl2]` 段，不要重复建两个相同段：

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
```

4. **保存工作并先停止 WSL 模型后**，在 PowerShell 执行：

```powershell
wsl --shutdown
wsl -d Ubuntu-22.04
```

`wsl --shutdown` 会停止所有 WSL 发行版及其中服务，不能边直播边执行。

5. Ubuntu 里重新测试 `curl -I https://github.com`。

`autoProxy` 主要接收 Windows 的 HTTP 代理配置，不保证识别每款 VPN 的所有流量策略。若代理软件只有 TUN 或未设置系统代理，仍需看其实际配置。

## 3. 手动设置当前 Ubuntu 终端的代理

先在代理软件查看 **HTTP/mixed 端口**，以下把 `7890` 当示例，必须换成你的实际值。

镜像网络模式，代理监听本机端口时：

```bash
source /mnt/c/AI/xiaoya-live-deploy-guide/scripts/wsl/proxy-session.sh http://127.0.0.1:7890
curl -I --connect-timeout 10 --max-time 30 https://raw.githubusercontent.com
```

NAT 模式下，WSL 的 `127.0.0.1` 通常指 WSL 自己。先找 Windows 宿主地址：

```bash
WIN_HOST=$(ip route show default | awk '{print $3; exit}')
source /mnt/c/AI/xiaoya-live-deploy-guide/scripts/wsl/proxy-session.sh "http://$WIN_HOST:7890"
```

NAT 连接宿主地址时，代理软件必须允许来自 WSL 网段的连接，且 Windows 防火墙允许这条连接；只在必要的本地范围开放，不要把代理公开到互联网。配置因软件而异，不知道时先用镜像网络或咨询该代理软件的官方说明。

如果只有 SOCKS 代理，curl 可用 `socks5h://HOST:PORT`，但 Python 下载器未必安装 SOCKS 支持；新手优先使用 HTTP/mixed 端口。

验证成功后再考虑写进 `~/.bashrc`。测试阶段先只影响当前终端，避免把错误配置永久写入。

撤销当前终端代理：

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

## 4. DNS 返回 0.0.0.0 怎么办

Ubuntu：

```bash
getent ahostsv4 raw.githubusercontent.com
grep -nEi 'github|githubusercontent' /etc/hosts
cat /etc/resolv.conf
```

Windows PowerShell：

```powershell
Select-String -Path "$env:SystemRoot\System32\drivers\etc\hosts" -Pattern 'github|githubusercontent'
Resolve-DnsName raw.githubusercontent.com -Type A
Resolve-DnsName raw.githubusercontent.com -Type A -Server 1.1.1.1 -DnsOnly -NoHostsFile
```

默认 DNS 返回 `0.0.0.0`，而指定其他 DNS 返回正常公网地址，说明默认解析链路在拦截或改写；**不等于模型下载链接失效**。继续检查代理软件 DNS、系统安全软件、路由器过滤、公司网络策略。WSL 的 `10.255.255.254` 可能是 DNS 隧道地址，本身不是故障证据。

`curl --resolve` 可用你当次正确解析到的 IP 做临时诊断，但不要把别人截图中的 GitHub IP 永久写进 hosts；IP 会变，且可能破坏其他访问路径。不要关闭 TLS 证书校验来掩盖 DNS 问题。

## 5. 下载成功还要验文件

完整下载示例：

```bash
curl -fL --connect-timeout 20 --max-time 120 "完整文件URL" -o downloaded.py
wc -l downloaded.py
head -n 5 downloaded.py
python -m py_compile downloaded.py
```

`py_compile` 成功不等于脚本一定会执行；若整份内容被压成一行并以 `#!` 或 `#` 开头，可能整行都成了注释。不要靠随意插换行修复 Python，重新从可信源码取文件并检查。API 返回的 base64 内容如果解码后还是一行，说明拿到的源文件本身就异常。

## 6. Git 和 Docker 是独立检查项

Windows Git 可在当前命令中使用代理，不必永久改所有仓库：

```powershell
git -c http.proxy=http://127.0.0.1:7890 ls-remote https://github.com/cyber-xiaoya/cyber-xiaoya-live.git HEAD
```

Docker pull 由 Docker Desktop/daemon 发请求，WSL 的 `http_proxy` 不一定控制它。要跑可选 DUIX 时，在 Docker Desktop 的代理设置里验证。`manifest not found` 通常是镜像/tag 不存在；`TLS handshake timeout` 才是连接或代理问题之一。不要把二者混为一谈。
