# 兼容性与验收边界

这是开发与迁移结果，不能替代四台设备上的实际验证。

| 项目 | 结果及限制 |
| --- | --- |
| 八个组 | 三套模板均只声明八个业务组；真实客户端导入后是否以同名识别，尚未全部实测。 |
| MiSub | 未重新部署或修改。没有从脱敏参考包取得真实地址，须在本地填写；每个客户端必须使用 MiSub 输出的适配格式，不能假定四端相同。 |
| Mihomo | 本机 Clash Verge 内核 v1.19.33 通过配置解析；隔离启动时 23 个规则提供器进入初始化，使用本机已有 ASN 数据库后未见规则解析错误。测试节点为临时值，未访问私人节点或公网业务。 |
| ASN 数据 | 部分上游使用 `IP-ASN`。内核需要 ASN.mmdb；首次下载失败时这些规则可能无法加载。确保客户端已有数据库，检查日志，不能仅看配置语法通过。 |
| Mihomo DoH | 模板用 `https://1.1.1.1/dns-query#LOCAL_SNELL` 指向本机 Snell 节点。真实节点、实际出口和 DNS 请求路径尚未验证；相关基础解析、网络与节点必须可用。 |
| Quantumult X DoH | 保留 Cloudflare DoH 和普通 DNS；未找到足够的官方依据证明当前版本可将内部 DoH 固定交给 Snell v5。不能声称已保留该行为。 |
| Shadowrocket DoH | 模板保留 Cloudflare DoH；Snell v5 和内部 DoH 按指定节点出站尚未实测，不能声称等价。 |
| DNS 覆盖 | Mihomo 生成只含域名类规则的 ChinaMax DNS provider，映射至阿里 DNS。Quantumult X 模板仅提供 BiliBili 的示例域名覆盖；Shadowrocket 模板未自动实现整套 ChinaMax DNS 覆盖。两端与 Surge 存在差异。 |
| DNS 劫持 | Mihomo 模板保留原配置的两个目标，但 `tun.enable` 默认关闭；只有启用客户端 TUN 后才可能生效。Quantumult X 和 Shadowrocket 的等价行为尚未核实。 |
| Grok 与链路 | 公共配置默认为 Intelligence。Mihomo 本地覆写示例可将其放到 `LOCAL_STATIC`；落地节点的 `dialer-proxy` 等字段须按真实协议填写。其他客户端的原生链路能力和 Snell v5 未验证。 |
| 私人规则和 Host | 原材料均为脱敏占位；未编造真实值。须在本地添加，且优先级需在设备核对。 |
| Shadowrocket 节点选择 | 模板用 `policy-regex-filter=.*` 将节点加入 Proxy，其他组可选 Proxy 或 DIRECT。尚未验证该版本能否同时为 Proxy 混入 DIRECT、或让每个业务组既引用 Proxy 又动态列出所有节点；当前模板不声称满足这两项。 |
| Quantumult X 规则优先级 | 本地例外、远程资源与 `final` 在实际版本中的顺序需要在规则判断界面验收。不得用 `host-keyword, ., Proxy` 代替 `final`，否则可能抢先匹配远程规则。 |
| Shadowrocket 规则优先级 | 当前模板的 RULE-SET 顺序跟随 Schema；实际编译结果、模块影响、精确域名与 IP 的优先级尚未在设备上确认。 |

截至当前缓存，转换时保留原始快照并显式报告未表达的类型：Mihomo 跳过 4 条 `URL-REGEX`、221 条 `USER-AGENT` 和 1 条逻辑 `OR`；Quantumult X 与 Shadowrocket 各跳过 4 条 `URL-REGEX`、57 条 `PROCESS-NAME` 和 1 条 `OR`。这条 Telegram `OR` 中的 ASN 也分别以独立规则存在；其它被跳过的规则不保证有等价替代。未来以上游与 `BUILD_REPORT.json` 为准。

上游的域名和 IP 有重叠；不能简单删除跨策略重复项，否则会改变首条匹配结果。大规则集在手机上的内存占用、电量和更新耗时尚未测量。Cloudflare、GitHub 和 MiSub 的可达性会因网络环境变化。

公开上游中有 3 条域名规则的域名包含 UUID 格式字符串：广告域名集 2 条、ChinaMax 1 条。它们来自公开上游，不代表用户节点凭据；为遵守“不上传 UUID”的明确要求，公开缓存和生成文件排除了这 3 条，计数见 `sources/cache/_omitted.json` 和 `dist/BUILD_REPORT.json`。这会分别减少对应的拦截或直连覆盖；同步时会继续过滤并更新计数。需要完整覆盖时，可在设备本地查阅原上游并补充，不能声称目前完全保留了所有原规则。
