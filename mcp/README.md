# FranChina MCP

该目录包含与 MkDocs 站点独立运行和部署的 FranChina Remote MCP。服务使用官方 MCP Python SDK v2 的 Streamable HTTP 传输，默认只监听 `127.0.0.1:8765`（loopback 模式），MCP 端点为 `/mcp`，健康检查端点为 `/health`。显式配置环境变量后可启用两种公网模式之一：Cloudflare Access 或多用户 API Key（见下文）。

> **认证边界：正式公网入口必须位于 Cloudflare 之后。** `mcp.franchina.qzz.io` 只能通过 Cloudflare Tunnel 暴露：要么走 Cloudflare Access（边缘完成 OAuth，origin 校验 `Cf-Access-Jwt-Assertion` JWT），要么走 API Key 模式（origin 校验每用户 `Authorization: Bearer` Key）。禁止在未接入任一认证模式的情况下通过 Nginx 或其他反向代理直接暴露 `/mcp`；不得以 query token、URL secret 或静态 URL 参数代替认证。默认 loopback 模式没有认证，仅限本机访问。

## 本地运行

```powershell
cd mcp
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python -m franchina_mcp.server
```

默认数据库为 `mcp/dev_rates.sqlite`。可通过 `FRANCHINA_MCP_DB_PATH` 指定其他位置：

```powershell
$env:FRANCHINA_MCP_DB_PATH = "C:\data\franchina\rates.sqlite"
```

生产环境的 systemd service 将该变量设置为 `/var/lib/franchina/rates.sqlite`。

## 工具

`save_exchange_rates` 接受 1～200 条汇率记录。字段语义固定如下：

- `currency` 是“被人民币定价的外币”，第一阶段只允许 `EUR` 和 `USD`，禁止使用 `CNY` 表示反向汇率；
- `rate` 只有一种含义：`1 currency = rate CNY`；
- 日期必须为 `YYYY-MM-DD`，汇率必须为正数，来源 URL 只允许 HTTP(S)。

例如，`currency=EUR, rate=7.8633` 表示 `1 EUR = 7.8633 CNY`。如果银行原网页采用“100 外币兑人民币”，调用方必须先除以 100：网页的 `100 EUR = 786.33 CNY` 应保存为 `currency=EUR, rate=7.8633`，MCP 字段中不得保存未标准化的 `786.33`。

请求示例：

```json
{
  "rates": [
    {
      "date": "2026-09-02",
      "source": "European Central Bank",
      "currency": "EUR",
      "rate_type": "reference",
      "rate": "7.8633",
      "source_url": "https://example.com/rates"
    }
  ]
}
```

返回值分别统计收到、插入、更新和未变化的记录数。同一 `date + source + currency + rate_type` 只保留一行；汇率和来源 URL 均未变化时不会执行 `INSERT` 或 `UPDATE`，`updated_at` 也保持不变。

## Transport Security

服务显式启用官方 `TransportSecuritySettings`，不会关闭 DNS rebinding protection。无认证 `main()` 固定使用 loopback 模式，只允许 `127.0.0.1`、`127.0.0.1:*`、`localhost`、`localhost:*`、`[::1]` 和 `[::1]:*`，不允许生产域名，任何 Origin 也不会进入白名单。

只有 `public=True` 并提供 `AuthorizationConfiguration`（SDK OAuth 路径）、`CloudflareAccessValidator`（Cloudflare Access 路径）或 `ApiKeyAuthenticator`（API Key 路径）**恰好之一**时，public 模式才额外允许 `mcp.franchina.qzz.io`、`mcp.franchina.qzz.io:*` 和精确的 `https://mcp.franchina.qzz.io` Origin。public 模式一个认证后端都不提供、或同时提供多个时，server factory 会直接抛出 `ValueError`，不会降级为无认证服务。

`GET /health` 固定返回 HTTP 200 和 `{"status":"ok"}`。该路由不读取或初始化数据库，也不执行汇率查询。loopback Host 的 `/health` 在任何模式下都不需要认证，部署 workflow 的健康检查因此不受认证影响；公网 Host 的 `/health` 在两种公网模式下都必须先通过认证。

## Cloudflare Access 公网模式（生产）

`FRANCHINA_MCP_MODE=cloudflare-access` 启用公网模式。该模式仅在显式配置以下环境变量后才能启动，**缺少任何一个都直接启动失败，绝不回退到无认证**：

| 环境变量 | 说明 |
| --- | --- |
| `FRANCHINA_MCP_MODE` | `loopback`（默认，未设置即 loopback）或 `cloudflare-access`；其他值启动失败 |
| `FRANCHINA_MCP_CF_TEAM_DOMAIN` | Cloudflare Access team domain，如 `franchina.cloudflareaccess.com`（可带 `https://` 前缀） |
| `FRANCHINA_MCP_CF_APPLICATION_AUD` | 保护 `mcp.franchina.qzz.io` 的 Access Application AUD 标签 |

认证流程：

1. Grok Custom MCP 访问 `https://mcp.franchina.qzz.io/mcp`，Cloudflare Access 在边缘完成 OAuth（Managed OAuth），未认证请求到不了 origin。
2. 认证通过后，Cloudflare 通过 Tunnel 把请求转发到本机 `127.0.0.1:8765`，并附带 `Cf-Access-Jwt-Assertion` 头（Access 签发的 RS256 JWT）。
3. origin 端 `CloudflareAccessMiddleware`（纯 ASGI，不影响 SSE 流式响应）要求：
   - 非 loopback Host（`mcp.franchina.qzz.io[:port]`）的一切请求必须携带合法 assertion；
   - loopback Host 的 `/mcp` 同样必须携带 assertion；
   - loopback Host 的 `/health` 保持开放，供 systemd 部署健康检查使用。
4. `CloudflareAccessValidator` 用 team domain 的官方 JWKS（`https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`，启动时加载、按 key id 缓存、轮换时限流刷新）做密码学校验：RS256 签名、`exp`、`nbf`/`iat`（如存在）、`aud` 必须等于配置的 Application AUD、`iss` 必须等于配置的 team domain。任何一步失败都返回 401，**只信任密码学校验结果，不信任 Header 是否存在**。
5. 校验通过后请求才进入 MCP 端点。本仓库不实现 OAuth Authorization Server，不签发 token，也没有 query token、固定 URL secret 或自定义登录协议。

启动失败条件（fail closed）：`FRANCHINA_MCP_MODE` 为未知值；`cloudflare-access` 模式下 team domain 或 AUD 缺失/非法；启动时 JWKS 端点不可达或返回无效内容。systemd 的 `Restart=on-failure` 会持续重试直至配置修复。

注意：公网模式下进程仍只监听 `127.0.0.1:8765`，外部流量必须经 Cloudflare Tunnel 进入；不要把该端口直接绑定到公网网卡或绕过 Access 暴露。

## API Key 公网模式（多用户，生产）

`FRANCHINA_MCP_MODE=api-key` 启用轻量的多用户 API Key 认证，适合通过 Cloudflare Tunnel 暴露给 Grok 等支持自定义 Bearer Header 的调用方。模式选择同样来自环境变量，但**具体用户 Key 绝不通过 Git、workflow 或环境变量配置**——只能在生产主机 shell 上用本地 CLI 生成。

| 环境变量 | 说明 |
| --- | --- |
| `FRANCHINA_MCP_MODE` | `api-key` 启用本模式；其他值见上表 |
| `FRANCHINA_MCP_AUTH_DB_PATH` | auth 数据库路径；生产固定为 `/var/lib/franchina/auth.sqlite`（systemd 注入），开发默认 `mcp/dev_auth.sqlite` |

密钥管理：

- Key 格式为 `fmcp_<key_id>_<random_secret>`：key_id 为 16 位 hex，secret 为 256-bit CSPRNG（64 位 hex）。
- **明文 Key 只在创建时打印一次**，之后无法找回；auth.sqlite 只保存 key_id 和 secret 的 SHA-256 摘要，认证时使用 constant-time 比较。高熵随机 secret 用固定摘要即可抵御暴力破解。
- auth 数据库与汇率数据库完全分离（不同文件、不同环境变量），保存字段：`key_id`、`name`、`key_hash`、`scopes`、`enabled`、`created_at`、`expires_at`（可空）、`last_used_at`。
- Key 与 `Authorization` 头不会写入日志；认证失败统一返回 401，不区分"未知 / 伪造 / 已禁用 / 已过期"。

本地管理 CLI（只能在服务器 shell 运行，不经 MCP 暴露，也没有任何远程 key 管理 tool）：

```bash
cd /opt/franchina-mcp/current
sudo -u ubuntu \
  FRANCHINA_MCP_AUTH_DB_PATH=/var/lib/franchina/auth.sqlite \
  /opt/franchina-mcp/.venv/bin/python -m franchina_mcp.keys create --name "Zhengyi" --scope rates:write

sudo -u ubuntu FRANCHINA_MCP_AUTH_DB_PATH=/var/lib/franchina/auth.sqlite \
  /opt/franchina-mcp/.venv/bin/python -m franchina_mcp.keys list

sudo -u ubuntu FRANCHINA_MCP_AUTH_DB_PATH=/var/lib/franchina/auth.sqlite \
  /opt/franchina-mcp/.venv/bin/python -m franchina_mcp.keys revoke <key_id>

# 可选：disable / enable（临时停用与恢复）
```

`create` 支持 `--scope`（可重复）与 `--expires-in-days`。**生产 Key 的创建与吊销绝不能由 GitHub Actions 完成。**

HTTP 认证（进程仍只监听 `127.0.0.1:8765`，外部流量经 Cloudflare Tunnel 进入）：

- `/mcp` 必须携带 `Authorization: Bearer <key>`；禁止 URL/query token。
- Header 缺失、格式错误、未知 key、已禁用、已过期 → 统一 HTTP 401。
- Key 合法但缺少工具所需 scope → HTTP 403：`save_exchange_rates` 需要 `rates:write`（scope 在 `tools/call` 时按工具检查，initialize/list 等发现性请求只需合法 Key）。
- DNS rebinding / Host allowlist 照常生效：public Host 仅允许 `mcp.franchina.qzz.io[:port]`，非法 Host 返回 421。
- loopback `/health` 无需认证（systemd/workflow 健康检查）；public `/health` 不开放（需认证）。

部署安全：`/var/lib/franchina/auth.sqlite` 不进入 Git（`.gitignore` 全局忽略 `*.sqlite`）、不进入 release 包（tar 已排除 `*.sqlite`）、部署流程不会覆盖/删除/重置它（`CREATE TABLE IF NOT EXISTS` 幂等，重开数据库保留既有 Key）；目录属主为运行 MCP 的 ubuntu 用户、权限 0750，unit 的 `UMask=0077` 保证库文件仅 ubuntu 可读写。

## Authorization 接入点

`AuthorizationConfiguration` 将 SDK v2 官方 `AuthSettings` 与 `TokenVerifier` 作为不可拆分的一组传给 `create_server(public=True, authorization=...)` 和对应的 transport settings factory。接入外部 Authorization Server 时，需要提供真实的 issuer、公开资源地址 `https://mcp.franchina.qzz.io/mcp`、所需 scope，以及能够校验签名或调用 token introspection、验证 audience 的 `TokenVerifier`。SDK 负责 Bearer token 验证入口、401 响应和 Protected Resource Metadata；本仓库不签发 token，也没有虚构授权服务器。

`CloudflareAccessValidator`（`franchina_mcp/cloudflare_access.py`）与 `ApiKeyAuthenticator`（`franchina_mcp/api_keys.py`）是当前选定的两条生产认证路径：前者在 Cloudflare 边缘认证、origin 只做 JWT 依赖方校验；后者在 origin 用独立 auth.sqlite 做多用户 Bearer 认证与按工具授权。两者都不走 SDK 的 Bearer/OAuth 中间件，也不对外公布 OAuth metadata。三条路径互斥，`create_server` 会拒绝同时提供多个认证后端的配置。loopback Host 判定、统一 401 响应等共享原语位于 `franchina_mcp/public_gate.py`。

## 部署边界

GitHub Actions 对 `mcp/README.md` 或 `mcp/tests/**` 的单独修改只运行测试，不构建 release、不上传、不切换 `current`、不 restart systemd。只有运行时代码、`mcp/requirements.txt`、`mcp/deploy/**` 或 MCP workflow 自身变化时才部署。

release 包只包含 `franchina_mcp/`、`requirements.txt` 和 systemd unit，不包含 README、测试或任何 SQLite 文件。生产数据库固定在 `/var/lib/franchina/rates.sqlite`，位于 release 目录之外。
