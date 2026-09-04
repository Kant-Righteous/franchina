# FranChina MCP

该目录包含与 MkDocs 站点独立运行和部署的 FranChina Remote MCP。服务使用官方 MCP Python SDK v2 的 Streamable HTTP 传输，默认只监听 `127.0.0.1:8765`（loopback 模式），MCP 端点为 `/mcp`，健康检查端点为 `/health`。显式配置环境变量后可启用 Cloudflare Access 公网模式（见下文）。

> **认证边界：正式公网入口必须位于 Cloudflare Access 之后。** `mcp.franchina.qzz.io` 只能通过 Cloudflare Tunnel + Access 暴露给 Grok Custom MCP 等外部调用方；OAuth 在 Cloudflare 边缘完成（Access Managed OAuth），origin 端对每个请求做 `Cf-Access-Jwt-Assertion` JWT 的密码学校验。禁止在未接入 Cloudflare Access 的情况下通过 Nginx 或其他反向代理直接暴露 `/mcp`；不得以 query token、URL secret 或静态 URL 参数代替 Access 认证。默认 loopback 模式没有认证，仅限本机访问。

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

只有 `public=True` 并提供完整 `AuthorizationConfiguration`（SDK OAuth 路径）或 `CloudflareAccessValidator`（Cloudflare Access 路径）之一时，public 模式才额外允许 `mcp.franchina.qzz.io`、`mcp.franchina.qzz.io:*` 和精确的 `https://mcp.franchina.qzz.io` Origin。public 模式两者都缺、或同时提供两者时，server factory 会直接抛出 `ValueError`，不会降级为无认证服务。

`GET /health` 固定返回 HTTP 200 和 `{"status":"ok"}`。该路由不读取或初始化数据库，也不执行汇率查询。loopback Host 的 `/health` 在任何模式下都不需要认证，部署 workflow 的健康检查因此不受 Access 认证影响。

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

## Authorization 接入点

`AuthorizationConfiguration` 将 SDK v2 官方 `AuthSettings` 与 `TokenVerifier` 作为不可拆分的一组传给 `create_server(public=True, authorization=...)` 和对应的 transport settings factory。接入外部 Authorization Server 时，需要提供真实的 issuer、公开资源地址 `https://mcp.franchina.qzz.io/mcp`、所需 scope，以及能够校验签名或调用 token introspection、验证 audience 的 `TokenVerifier`。SDK 负责 Bearer token 验证入口、401 响应和 Protected Resource Metadata；本仓库不签发 token，也没有虚构授权服务器。

`CloudflareAccessValidator`（`franchina_mcp/cloudflare_access.py`）是当前选定的生产认证路径：认证发生在 Cloudflare 边缘，origin 只做 JWT 依赖方校验，因此不走 SDK 的 Bearer/OAuth 中间件，也不对外公布 OAuth metadata。两条路径互斥，`create_server` 会拒绝同时提供两者的配置。

## 部署边界

GitHub Actions 对 `mcp/README.md` 或 `mcp/tests/**` 的单独修改只运行测试，不构建 release、不上传、不切换 `current`、不 restart systemd。只有运行时代码、`mcp/requirements.txt`、`mcp/deploy/**` 或 MCP workflow 自身变化时才部署。

release 包只包含 `franchina_mcp/`、`requirements.txt` 和 systemd unit，不包含 README、测试或任何 SQLite 文件。生产数据库固定在 `/var/lib/franchina/rates.sqlite`，位于 release 目录之外。
