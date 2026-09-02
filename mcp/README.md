# FranChina MCP

该目录包含与 MkDocs 站点独立运行和部署的 FranChina Remote MCP。服务使用官方 MCP Python SDK v2 的 Streamable HTTP 传输，只监听 `127.0.0.1:8765`，MCP 端点为 `/mcp`，健康检查端点为 `/health`。

> **认证状态：尚未达到公网可用条件。** 当前启动入口只用于 loopback 本地访问，尚未接入外部 OAuth 2.1 Authorization Server 和生产 `TokenVerifier`。**公网反代前必须完成认证**；在此之前禁止通过 Nginx 或其他反向代理暴露写工具。不得以 query token、URL secret 或静态 URL 参数代替 MCP Authorization。

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

只有同时设置 `public=True` 并提供完整 `AuthorizationConfiguration` 时，public 模式才额外允许 `mcp.franchina.qzz.io`、`mcp.franchina.qzz.io:*` 和精确的 `https://mcp.franchina.qzz.io` Origin。public 模式缺少 `AuthSettings` 或可调用的 `TokenVerifier` 时，server factory 会直接抛出 `ValueError`，不会降级为无认证服务。

`GET /health` 固定返回 HTTP 200 和 `{"status":"ok"}`。该路由不读取或初始化数据库，也不执行汇率查询。

## Authorization 接入点

`AuthorizationConfiguration` 将 SDK v2 官方 `AuthSettings` 与 `TokenVerifier` 作为不可拆分的一组传给 `create_server(public=True, authorization=...)` 和对应的 transport settings factory。未来接入外部 Authorization Server 时，需要提供真实的 issuer、公开资源地址 `https://mcp.franchina.qzz.io/mcp`、所需 scope，以及能够校验签名或调用 token introspection、验证 audience 的 `TokenVerifier`。SDK 负责 Bearer token 验证入口、401 响应和 Protected Resource Metadata；本仓库目前不签发 token，也没有虚构授权服务器。

完成上述外部集成并通过认证测试之前，systemd 启动的无认证 loopback 实例不能被描述或用作生产公网 MCP。

## 部署边界

GitHub Actions 对 `mcp/README.md` 或 `mcp/tests/**` 的单独修改只运行测试，不构建 release、不上传、不切换 `current`、不 restart systemd。只有运行时代码、`mcp/requirements.txt`、`mcp/deploy/**` 或 MCP workflow 自身变化时才部署。

release 包只包含 `franchina_mcp/`、`requirements.txt` 和 systemd unit，不包含 README、测试或任何 SQLite 文件。生产数据库固定在 `/var/lib/franchina/rates.sqlite`，位于 release 目录之外。
