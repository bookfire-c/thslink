# ThsLink 调用说明

ThsLink 仅供个人非商业学习与研究使用，不允许用于商业行为；完整条款见 [项目许可](../LICENSE.md)。

ThsLink 把桌面操作、HTTP 请求和 CLI 命令送到同花顺 `xiadan.exe` 内的桥接 DLL，通过命令框提交，后台接收钩子回执。

## 启动与接口设置

先启动同花顺并登录账户，再启动 ThsLink。首次使用时打开主界面的“接口”开关；开关状态会保存，以后启动自动恢复，手动关闭后下次保持关闭。

- 默认地址：`http://127.0.0.1:8421`。
- 设置中可以修改监听 IP、端口和 API 密钥。
- 局域网调用：监听 IP 设为 `0.0.0.0`，其他电脑使用运行 ThsLink 电脑的局域网 IP 和端口；Windows 防火墙须允许该端口。`0.0.0.0` 是监听配置，不是客户端请求地址。
- 配置密钥后，每次请求携带 `X-API-Key: 你的密钥`。
- 开关、地址、端口及密钥保存在 `%APPDATA%/thslink/ui-settings.json`；绿色便携版更新不覆盖配置。同一 Windows 用户移动软件目录后也继续使用已有配置。
- 关闭“手动交易”后，停止自动读票、股票跟随与交易热键，界面显示“读票暂停”；HTTP 请求、DLL 连接维护和后台回执继续工作。重新开启手动交易后恢复读票。

命令行 `thslink.exe ui --http` 启动界面和 HTTP；`thslink.exe serve` 仅运行 HTTP，使用默认本机地址。自定义监听配置请在桌面设置中使用。

## 接口一览

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/order` | 提交单笔买入、卖出或撤单 |
| POST | `/orders/batch` | 一次提交 1～20 笔请求 |
| GET | `/orders/:id` | 用 request_id 查询单笔回执 |
| GET | `/batches/:id` | 用 batch_id 查询整批及逐笔状态 |
| GET | `/health` | DLL 连接状态 |
| GET | `/who` | 账户信息 |
| GET | `/last` | 最新回执，供诊断使用 |
| GET | `/receipts/unmatched` | 无法确定归属的回执，供诊断使用 |

## 单笔请求

以下 JSON 发送到 `POST /order`：

```json
{"side":"buy","code":"000009","price":"mrxjg","amount":100,"notip":true}
```

| 参数 | 填写要求 | 含义与示例 |
|---|---|---|
| side | 必填 | buy 买入、sell 卖出、cancel 撤单 |
| code | 必填 | 六位股票代码字符串；全撤填 all |
| price | 买卖必填 | 价格关键字或指定价格字符串，例如 mrxjg 或 "7.00"；撤单不填 |
| amount | 买卖数量五选一 | 股数，正整数；1 手填 100 |
| m | 买卖数量五选一 | 金额，单位元 |
| cw | 买卖数量五选一 | 买入按可用资金比例；卖出按可卖数量比例 |
| zzc | 买卖数量五选一 | 本次交易金额占账户总资产的比例 |
| zcw | 买卖数量五选一 | 交易后这只股票还剩多少仓位（占账户总资产）；卖出填 0 表示清仓 |
| account | 可选 | 省略：当前账户；ACCOUNT_ID：指定已登录账户；all：全部已登录账户 |
| notip | 可选，自动调用推荐 true | 跳过同花顺确认提示 |
| zdky | 可选，仅买入 | 资金不足时按最大可买数量提交 |

数量参数只选一种。cw、zzc、zcw 支持小数或分数；小数 0.1 是 10%，分数须写字符串 "1/10"。zcw 是交易后的目标仓位，不是这次交易的比例。

| 价格关键字 | 含义 |
|---|---|
| mrxjg / mcxjg | 买限价 / 卖限价 |
| mrj1～mrj5 | 买一～买五 |
| mcj1～mcj5 | 卖一～卖五 |
| zxjg | 最新价 |
| ztjg / dtjg | 涨停价 / 跌停价 |
| "7.00" | 自定义每股价格 7 元 |

撤单不填写价格和数量：

```json
{"side":"cancel","code":"000009","notip":true}
```

全撤当前账户：

```json
{"side":"cancel","code":"all","notip":true}
```

全撤全部已登录账户：

```json
{"side":"cancel","code":"all","account":"all","notip":true}
```

`code=all` 是全撤委托；`account=all` 是全部已登录账户，二者作用不同。指定账号时将 ACCOUNT_ID 替换为实际账号。买入、卖出、撤单均可选择当前、指定或全部已登录账户。

## 批量买入及其他批量操作

发送到 `POST /orders/batch`，将每笔单笔 JSON 放进 orders 数组：

```json
{
  "orders": [
    {"side":"buy","code":"000009","price":"mrxjg","amount":100,"notip":true},
    {"side":"buy","code":"600000","price":"mrxjg","cw":"1/10","notip":true}
  ]
}
```

每批 1～20 笔；每笔分别设置方向、股票、价格、数量和 account。省略账户时使用当前账户；指定账户要写在每笔中。批量提交不是原子事务：一笔失败不会撤回其他已提交的委托。各笔比例按交易端处理时的账户数据计算，不是固定同一资金快照。

返回 batch_id 和 orders，各笔 result 为提交结果。保存 batch_id，再用 `GET /batches/批次编号` 查询。批量合并回执按整批展示；不能仅凭返回数组顺序判断合同号属于哪笔订单。

```python
import requests

base = "http://127.0.0.1:8421"
headers = {}  # 配置密钥后填写 {"X-API-Key": "你的密钥"}
payload = {"orders": [
    {"side": "buy", "code": "000009", "price": "mrxjg", "amount": 100, "notip": True},
    {"side": "buy", "code": "600000", "price": "mrxjg", "cw": "1/10", "notip": True}
]}
response = requests.post(base + "/orders/batch", json=payload, headers=headers, timeout=30)
response.raise_for_status()
result = response.json()
print(result)
batch_id = result.get("batch_id")
if batch_id is not None:
    print(requests.get(base + f"/batches/{batch_id}", headers=headers, timeout=10).json())
# 等待中，继续查询原批次编号，不要重复提交整批。
```

软件“说明”的第二页“HTTP 请求生成/在线调试”支持单笔和批量：表单逐笔“加入批量”，或直接编辑 orders JSON，再复制 JSON / Python / cURL 代码。发送按钮会提交实际请求，下方自动查询回执。

## 结果与日志

单笔返回 request_id、accepted、confirmed、status，以及 receipt 或 error。accepted 表示请求被接收；confirmed 表示回执确认。查询接口用原 request_id，不要拿 `/last` 代替。

批量查询各笔 stage：Posted 等待回执，Submitted 回执完成，Failed 请求失败，Timeout 结果暂未确定（可继续查询迟到回执）。HTTP 请求失败或等待超时，不代表同花顺一定没有收到，请先查原编号再决定下一步。

回执在后台处理。软件已结束历史保留本次运行最近 200 条，未完成请求单独保留（最多 2000 条）；清空历史不会清掉仍需处理的请求，不保存交易流水到磁盘，重启后清空。需要长期日志时，由调用程序保存请求参数、返回编号和查询结果。复制生成代码本身不发单。

## CLI 命令

```text
thslink.exe send buy 000009 mrxjg -cw 1/10 -notip
thslink.exe send sell 000009 mcxjg -cw 1/2 -account ACCOUNT_ID -notip
thslink.exe send cancel all -notip
thslink.exe send cancel all -account all -notip
thslink.exe result 请求编号
thslink.exe who
```

CLI 与 HTTP 使用同一 DLL 通道；HTTP 字段 account、cw 等对应命令的 -account、-cw 等。

## 重连与更新

同花顺重启后，软件重新识别进程并建立连接。DLL 重连按停止后台线程、解除钩子、卸载、重新加载的顺序执行；有发送、排队或等待回执请求时不允许完整重启。

GitHub 更新只在用户手动点击检查时执行，不会启动或定时自动检查。更新来源已内置，无需填写仓库地址。更新使用完整便携包，同时替换主程序、DLL 和加载器；安装前退出同花顺，个人配置保留。更新请确保网络可以访问 GitHub。


## 长期运行与技术诊断

未匹配提示的诊断缓存保留最近 500 条、最长 1 小时。请求结果记录最多 2000 笔；容量不足时回收已结束或超时超过 5 分钟的记录，批量记录一起回收。超时仍表示结果未知，不自动重发。软件后台对旧请求的自动查询最多持续 5 分钟。

回执处理积压时暂停接收新单，优先处理已捕获的回执，不删除正常回执；稍后可重新提交被明确拒绝的请求。

技术文件日志默认关闭。如需排查问题，在 `%LOCALAPPDATA%\ThsLink\diagnostics` 创建空文件 `enabled`；删除该文件即可关闭，约 5 秒内生效。该目录下 `bridge.log`、`timing.log` 各最多 1 MB，并各保留 3 份轮换备份。这些是技术诊断文件，不是持久交易日志。


## 请求容量与超时

- HTTP 同时允许最多 64 个待处理或执行中的调用（单笔、批量和查询共用容量）。满额立即拒绝；被拒请求不会延后自动发送。
- HTTP 请求等待发送的有效期为 5 秒。在取得发送锁后、实际写入交易命令前再次检查；过期或 HTTP 服务已经停止时返回“本次未发送”。服务重启后，上一轮尚未发送的请求也不会继续发送。
- 已经写入交易命令后，通信超时仅表示结果未知，禁止自动重发。调用方应核对回执或委托状态。
- 客户端每次管道通信有 10 秒期限，DLL 客户端请求读取和响应写入各有 5 秒期限。分段读取完整消息；超过 64 MB 时明确报错，不伪装为空回执。
- 未知结果继续查询最多 5 分钟。超过该保留期后，记录仍表示未知，但不再永久阻止安全重连；重连不会重发旧单，也不会将其改成成功。
- 钩子积压 1024 条是暂停接收新单的门槛，不是丢弃回执的硬容量上限；已经捕获的回执继续按顺序处理。
