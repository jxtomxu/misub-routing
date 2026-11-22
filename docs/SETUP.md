# 四个客户端安装说明

**请先保留当前可用配置，再以新配置单独测试。** 公开文件不包含 MiSub 地址、自建节点或私人例外；节点协议支持、DNS 实际出站和静态链需要在各设备核验。本项目还没有完成四个客户端的实机验收，限制见 [COMPATIBILITY.md](COMPATIBILITY.md)。

## 先准备

1. 在自己的 MiSub 中获取相应客户端格式的节点订阅：Quantumult X、Mihomo、Shadowrocket 分别确认输出格式；Clash Verge 和 FlClash 都使用 Mihomo 格式。不要把真实链接发到公开仓库或 Issue。
2. 准备自己的 Snell 节点参数、静态落地节点及链路配置。参考包中的地址和口令是示例，不能使用。私人 IP、私人域名、Host 与 Emby 地址也须从自己的资料取得。
3. 测试时先确认 GitHub raw 地址可从设备访问。节点订阅和规则资源应分别更新，不要把两者合并成一条公开链接。

公开规则基础地址：

```text
https://raw.githubusercontent.com/jxtomxu/misub-routing/main/dist/
```

## Quantumult X

1. 取得 `dist/quantumult-x/config.template.conf`，复制为设备本地配置。该模板的 `[filter_remote]` 已逐个指向 GitHub 的公开规则集；保留规则集的先后次序。
2. 在本地 `[server_remote]` 中填入 MiSub 的 Quantumult X 订阅地址，并设置资源标签 `MiSub`，更新间隔可用 `3600` 秒。也可在 App 的节点订阅界面添加并使用同一标签。真实 URL 只留在设备上。
3. 在本地 `[filter_local]` 添加自己的私人域名、IP 例外和落地节点相关规则。若当前 Quantumult X 版本支持所需链路，可将 Grok 的特例放在公开规则之前；不支持时保留 Intelligence 并自行选择节点。
4. 选择新配置，在 `Proxy` 中选择一个真实节点。`Intelligence`、`Telegram`、`YouTube`、`Google`、`GlobalMedia` 默认指向 Proxy；`BiliBili` 和 `Emby` 默认 direct。确认实际显示八组且 MiSub 节点出现。
5. 检查远程资源自动更新开关和 `update-interval=86400`；在资源列表手动刷新一次，核对更新时间和失败数。再用规则判断或连接记录检查 ChatGPT、Google、BiliBili 与 LAN 的实际命中。`final` 与远程资源优先级必须在当前版本确认。

此端当前仅提供 BiliBili 域名的阿里 DNS 覆盖示例，不等价于完整 ChinaMax DNS 覆盖；DoH 固定 Snell 尚未验证。

## Clash Verge

1. 导入以下公开配置 URL，先不要切换为正在使用的配置：

```text
https://raw.githubusercontent.com/jxtomxu/misub-routing/main/dist/mihomo/config.template.yaml
```

2. 打开该配置的脚本覆写，复制 `clients/clash-verge/local-override.example.js` 的内容到应用本机编辑器。把 MiSub 的 **Mihomo** 节点订阅填入 `subscriptionUrl`。按自己的节点参数填写名为 `LOCAL_SNELL` 的节点对象，以及名为 `LOCAL_STATIC` 的落地节点对象；若需要代理链，按 Mihomo 对应协议填写 `dialer-proxy`。在 `privateRules` 中填写私有例外。示例里的 `null` 和空字符串是等待填写的占位值。
3. 保存并为这个配置启用脚本覆写，再预览最终配置。确认 `proxy-providers.MiSub.url` 是自己的本地值，两个节点引用存在，且没有意外的额外策略组。不要将填好后的脚本提交 GitHub。
4. 启用配置前确认 ASN 数据库存在。查看应用日志中规则提供器是否加载，尤其是 `IP-ASN`、ChinaMax DNS provider 和节点链。选择实际节点：模板中的 `Proxy` 初始项为 `REJECT`，需要手动改选；其他组默认如前所述。
5. 在订阅设置中开启公开配置自动更新；MiSub provider 的 `interval` 为 3600 秒，各规则 provider 为 86400 秒。可从配置页手动更新配置和 provider，再检查更新时间。若需要 DNS 劫持，按设备情况启用 TUN 后检查相应配置；模板默认关闭 TUN。

远程配置更新后的覆写顺序和 UI 名称可能随版本变化；先看配置预览，再验收真实 DNS 与出口。不能用示例节点验证实际 Snell 或静态链。

## FlClash

1. 在配置页从 URL 添加与 Clash Verge 相同的 `dist/mihomo/config.template.yaml` 地址。不要立即替换正在使用的配置。
2. 打开工具中的脚本管理，复制 `clients/flclash/local-override.example.js`，只在应用本地填入自己的 MiSub、Snell、静态节点与私人规则。
3. 回到该远程配置的更多操作，选择覆写、脚本，并明确启用刚保存的脚本。FlClash 使用 JavaScript 覆写，不直接使用 Clash Verge 的 Merge YAML。不同版本界面可能不同。
4. 预览或检查最终配置，确认八组、节点 provider、`LOCAL_SNELL`、`LOCAL_STATIC`、规则集和 ASN 数据库；在 Proxy 中手动选择真实节点。核对 FlClash 的全局 DNS / TUN 覆写没有覆盖本配置中需要的设置。
5. 开启该 URL 配置的自动更新；节点和规则 provider 使用各自的间隔。手动更新一次，查看日志和资源更新时间，再逐项核对实际命中与出口。

FlClash 未在本次设备上实测。若导入时应用先验证占位配置、无法启用本地脚本，请先在本地创建带真实私人节点的副本测试；结构性更新可能需要重新合并。

## Shadowrocket

1. 在 App 的节点页添加 MiSub 的 **Shadowrocket** 格式订阅并更新。不要把订阅地址写入公开配置。
2. 获取 `dist/shadowrocket/config.template.conf`，导入为一个新配置并保留现有可用配置。模板中的 `RULE-SET` 指向 GitHub 分别生成的规则列表。
3. 在设备本机把私人域名、IP、Emby 和 Grok 例外加在公开规则前；按当前版本的节点链功能配置自己的静态落地。
4. `Proxy` 的 `policy-regex-filter=.*` 用于选择已导入节点；确认实际节点确实出现在组内。当前模板的 Proxy 不含 DIRECT，其余业务组提供 Proxy 和 DIRECT；每个业务组直接列出全部节点的行为尚未验证。确认名称 `Proxy` 没有与客户端内置策略发生冲突。
5. 在配置或规则集设置中开启自动更新，手动更新或编译一次，核对规则列表数量和更新时间。打开规则判断或连接记录，检查 AI、YouTube、Google、BiliBili、国内域名与 LAN 命中，再确认真实出口。

Cloudflare DoH、完整 ChinaMax DNS 覆盖以及 DoH 经 Snell 的等价功能尚未实测；不要把模板中的 DNS 设置当成已验收的 Surge 等价配置。

## 更新成功如何确认

分别看 MiSub 节点订阅、GitHub Actions 最近成功时间和客户端规则资源时间。选一个上游或本仓库最近变化的域名，在客户端规则判断中确认命中与策略组，再检查实际出口。规则文件已下载不等于规则已经生效；失败时保留旧配置并查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。
