<p align="center"><img src="docs/icon.svg" width="88" alt="ThsLink 红牛图标"></p>

# ThsLink

同花顺快捷下单与 HTTP 接口下单工具，支持桌面按钮、热键快捷下单，以及通过 HTTP 接口买入、卖出、撤单和查询账户数据。

支持本机、局域网及服务器远程 HTTP 调用：同花顺和 ThsLink 可运行在同一台 Windows 服务器上，你的电脑或另一台服务器通过 VPN 或 HTTPS 入口发送请求，无需处于同一局域网。

Windows 绿色便携版，解压后双击 `thslink.exe`，无需安装。

**当前版本：v0.2.5。仅供个人非商业学习与研究，禁止用于任何商业行为。本仓库提供成品和说明，不包含应用源码。**

[下载最新版](https://github.com/electkismet/thslink/releases/latest) · [完整 HTTP 使用说明](docs/HTTP.md) · [Python 示例](examples/http_demo.py) · [更新记录](CHANGELOG.md) · [许可](LICENSE.md)

## 界面预览

**桌面快捷下单**

![ThsLink v0.2.0 主窗口：快捷按钮、账户选择与 HTTP 接口开关](docs/images/main.png)

## 支持什么

| 功能 | 说明 |
|---|---|
| 调用位置 | 本机、局域网、服务器远程调用；远程网络通过 VPN 或自行配置的 HTTPS 入口接入 |
| 买入、卖出、撤单 | 单笔请求，或一次提交 1～20 笔；指定股票撤单、全撤 |
| 多账户 | 当前账户、指定已登录账户、全部已登录账户；批量中每笔可分别设置 |
| 数量与比例 | 股数、金额、可用资金 / 可卖数量比例、总资产比例、交易后的目标仓位 |
| 数据查询 | 持仓、当日委托、当日成交、资金；POST JSON 或 GET 参数二选一 |
| 原始结果 | HTTP 保留内部查询返回的原始字段和值，按账户与结果表组织 |
| 请求跟踪 | 保存 request_id、batch_id 或 query_id，按对应编号获取后续结果 |
| 连接复用 | HTTP Keep-Alive；程序与 DLL 使用本机管道长连接 |
| 桌面操作 | 快捷按钮、组合热键、批量委托、查询抽屉、交易与运行日志、手动输入股票 |
| 窗口与主题 | 浅色 / 暗黑、窗口置顶；最小化到任务栏，关闭到托盘，单击托盘恢复 |
| 更新 | 仅在用户手动点击时检查 GitHub，完整便携包更新，保留配置 |

## 下载与启动

1. 下载 Release 中的 **`thslink-windows.zip`**，解压到有写入权限的目录。GitHub 自动生成的 Source code 压缩包不是程序包。
2. 先启动同花顺并登录交易账户，再双击 `thslink.exe`。主程序、`thslink_bridge.dll` 和 `thslink-load.exe` 须放在同一目录。
3. 运行环境为 Windows 10/11 x64，桥接组件用于 32 位 `xiadan.exe`。内部接口与交易端版本有关，不匹配时会拒绝连接。
4. 打开主窗口“接口”开关。只用 HTTP 时，可以关闭“手动交易”，暂停自动读票和交易热键。

虚拟机或远程桌面遇到窗口黑屏时，退出 ThsLink 后双击包内 `兼容运行.bat`，使用带系统标题栏的兼容窗口。普通双击 EXE 仍使用无边框窗口。兼容模式不保证解决所有显卡或虚拟机渲染问题。

配置保存在 `%APPDATA%/thslink/ui-settings.json`。接口开关会保存，下次启动恢复；升级和移动程序目录不会清空该 Windows 用户的配置。

**从旧版升级，请先退出 ThsLink 和同花顺交易端，整体替换便携包，再重新启动。**不要只换 EXE 或把新旧 DLL 混用。

## HTTP 快速上手

默认地址：`http://127.0.0.1:8421`。请求体为 JSON，设置密钥后携带 `X-API-Key`。

先查持仓，发送到 `POST /query`：

```json
{"kind":"holdings","account":"current","wait_ms":2000}
```

`kind` 可改为 `orders`（当日委托）、`deals`（当日成交）、`funds`（资金）。返回 `pending` 时，使用原 `query_id` 请求 `GET /queries/编号`，不要重新发起同一查询。

买入 100 股，发送到 `POST /order`（会实际提交买入委托）：

```json
{"side":"buy","code":"000009","price":"mrxjg","amount":100,"notip":true}
```

卖出将 `side` 改为 `sell`、`price` 改为 `mcxjg`。撤单不填价格和数量，例如全撤全部已登录账户：

```json
{"side":"cancel","code":"all","account":"all","notip":true}
```

`code=all` 选择撤单范围，`account=all` 选择账户范围；两个字段作用不同。

### 多账户与比例

| 填法 | 含义 |
|---|---|
| 省略 account | 交易使用同花顺当前账户；查询默认 current |
| `"account":"ACCOUNT_ID"` | 将占位符替换为实际已登录账户号 |
| `"account":"all"` | 当前交易端全部已登录账户，不自动登录其他账户 |
| `"cw":"1/10"` | 买入按可用资金 10%；卖出按可卖数量 10% |
| `"zzc":0.1` | 本次买卖金额占账户总资产 10% |
| `"zcw":0.25` | 交易后这只股票还剩多少仓位：目标为总资产的 25% |

`amount`、`m`、`cw`、`zzc`、`zcw` 五选一。比例支持小数和字符串分数，例如 `0.1` 或 `"1/10"`。指定账户无需先切换同花顺当前账户。

### 批量请求

发送到 `POST /orders/batch`，每批 1～20 笔，每笔单独设置参数和账户：

```json
{"orders":[
  {"side":"buy","code":"000009","price":"mrxjg","amount":100,"notip":true},
  {"side":"buy","code":"600000","price":"mrxjg","cw":"1/10","notip":true}
]}
```

批量不是原子事务：一笔失败不会撤回其他已提交的委托。保存 `batch_id`，再用 `GET /batches/编号` 查看逐笔结果。

### 接口速查

| 方法与路径 | 用途 |
|---|---|
| `POST /order` | 单笔买入、卖出、撤单 |
| `POST /orders/batch` | 批量提交 |
| `GET /orders/:id` | 用 request_id 查询单笔回执 |
| `GET /batches/:id` | 用 batch_id 查询整批及逐笔状态 |
| `POST /query` | JSON 主动查询：kind、account、wait_ms |
| `GET /query/:kind` | GET 方式主动查询，与 POST 返回一致 |
| `GET /queries/:id` | 用 query_id 读取同一次查询结果 |
| `GET /health` | 检查连接状态 |
| `GET /who` | 获取账户信息 |
| `GET /last` | 最新回执，仅供诊断，不代替按编号查询 |

查询结果在 `accounts → tables → rows` 中；检查 `status`、`complete` 及账户错误，不能仅看 HTTP 200。只有收到完整空表才表示没有记录；缺失字段不能当作数值 0。分页和容量边界见[完整说明](docs/HTTP.md)。

## Python 连续调用

服务端默认支持 HTTP Keep-Alive。你的 Python 程序启动时创建一次 `requests.Session()`，下单、查询和轮询都使用同一个 Session，程序退出时再关闭。软件生成的 Python 代码与[示例文件](examples/http_demo.py)均采用这个方式。

不要每次调用都重新创建客户端；仅添加 `Connection: keep-alive` 请求头不能代替复用。网络中断后后续调用可以重新建连接，**交易 POST 超时不能盲目重发**：上一笔可能已提交，应先查回执或当日委托。

## 局域网与远程调用

同花顺和 ThsLink 运行在同一台 Windows 电脑上，其他电脑通过 HTTP 调用，无需安装同花顺或 ThsLink。

1. 在设置中允许局域网访问，将监听地址设为 `0.0.0.0`，配置端口与 API 密钥，修改后重启接口。
2. 调用端使用服务端实际 IP，例如 `http://192.168.1.100:8421`；Windows 防火墙允许所需来源访问。
3. `127.0.0.1` 只访问调用端本机，`0.0.0.0` 仅用于监听，不能当作远程调用地址。

通过公网调用时，可使用 VPN 组网后访问 VPN 地址，或自行配置带身份认证的 HTTPS 入口。程序本身提供 HTTP，未内置 HTTPS 证书或 VPN。接口用法保持一致。

## 更新与数据保存

用户手动检查、下载和安装更新，没有启动检查或定时检查。**更新请确保网络可以访问 GitHub。**更新器匿名访问 Release；仓库为私有时，需登录具有权限的 GitHub 账号手动下载，软件内检查不可用；仓库公开后可使用软件内检查。

软件内交易历史用于查看本次运行状态，不持久保存交易流水。需要长期记录时，由调用程序保存请求、编号与回执。账户配置、密钥、技术日志和源码不随便携包分发。

## 许可

ThsLink 仅允许个人非商业学习研究使用，禁止商业用途，未经书面许可不得再分发。详见 [LICENSE.md](LICENSE.md)。这不是开源许可证；第三方组件依其各自许可证使用，见[第三方许可说明](docs/THIRD_PARTY_NOTICES.md)。
