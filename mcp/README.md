# FranChina MCP

该目录是与 MkDocs 站点独立运行和部署的 FranChina 远程 MCP 服务，基于官方 MCP Python SDK，用于接收和保存多来源汇率数据。

## 本地运行

```powershell
cd mcp
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python -m franchina_mcp.server
```

本地默认只监听本机回环地址，不启用认证，仅供开发调试。汇率数据库默认为 `mcp/dev_rates.sqlite`，可通过环境变量 `FRANCHINA_MCP_DB_PATH` 指定其他位置。

## 工具

`save_exchange_rates` 接受一批汇率记录，字段约定如下：

- `currency` 是被人民币定价的外币，目前只允许 `EUR` 和 `USD`，不使用 `CNY` 表示反向汇率；
- `rate` 只有一种含义：`1 currency = rate CNY`；
- 日期格式为 `YYYY-MM-DD`，汇率必须为正数，来源 URL 只允许 HTTP(S)。

例如 `currency=EUR, rate=7.8633` 表示 `1 EUR = 7.8633 CNY`。银行网页若按“100 外币兑人民币”标价，调用方需先除以 100 再提交。

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

返回值统计收到、插入、更新和未变化的记录数。同一日期、来源、币种和汇率类型只保留一条记录，内容未变化时不会重复写入。

## 安全原则

- 公网访问必须经过认证网关，服务不会在缺少认证配置时以无认证方式对外提供；认证配置不完整时直接拒绝启动。
- 认证凭据只在服务器本机管理，不进入 Git、CI 配置或日志。
- 启用 DNS rebinding 防护，只接受预期的 Host 与 Origin。
- 健康检查端点不读取数据，仅供部署流程确认服务状态。

## 部署

部署由 GitHub Actions 完成：只修改文档或测试时仅运行测试；运行时代码、依赖或部署配置变化时才构建并发布。发布包不包含文档、测试和数据库文件，生产数据保存在发布目录之外。
