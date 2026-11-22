# 架构与迁移说明

```text
公开上游 ──每日同步──> sources/cache ──校验──> schema/routing.yaml + 三套生成器
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
          Quantumult X 集合               Mihomo providers             Shadowrocket 集合
                 └──────────────────────── 设备本机 ──────────────────────────┘
                                      ▲
                         MiSub 节点订阅与本地私人配置
```

`schema/routing.yaml` 是业务组、规则顺序、DNS、上游和客户端选项的唯一公开来源。`routing.schema.json` 约束字段，构建程序额外校验八个组、唯一 ID、优先级和引用。`sources/cache` 是公开上游的最后有效快照，每份文件分开保存。每个上游的 URL、授权和内容摘要记录在 `dist/BUILD_REPORT.json`。

公开配置不包含真实 Snell、静态落地、MiSub 地址、私人 Host、私人 IP 或私人域名。上游公开规则和文档中可能含公共 IP、标准 LAN 网段及公开域名，这些不代表用户的私人配置。脱敏参考里的节点、地址及私人域名示例没有被当成真实数据迁入。

## 优先级与映射

规则按 `priority` 排序。私人例外由设备本地放在公开规则之前。公开规则依次处理明确例外、广告、AI、中国区 Apple、Emby、Apple/GitHub/Microsoft/Telegram/游戏/YouTube、流媒体、BiliBili、中国媒体、GlobalMedia、Google、Proxy、ChinaMax、LAN 和最终 Proxy。各客户端的规则类型与实际引擎匹配顺序仍需实机核对。

| 原有策略 | 新出口 | 原因 |
| --- | --- | --- |
| Apple | DIRECT | 原配置首选 DIRECT；参考 Mac 当时实际选中 Proxy，本次按用户明确要求采用默认直连。 |
| Netflix、Disney+、Spotify、TikTok | GlobalMedia | 原配置四组首选均为 Proxy，统一组首选 Proxy。 |
| Microsoft | DIRECT | 原配置首选 DIRECT；Copilot 的明确 AI 域名优先进入 Intelligence。 |
| Gamer：Epic、Sony、Steam、Nintendo | DIRECT | 原配置首选 DIRECT。 |
| 香港、美国、日本、韩国、台湾、新加坡 | 不生成组 | 节点通过 MiSub provider 或客户端订阅进入现有组，不再建立地区组。 |
| 我的节点、自建、静态落地 | 节点或节点来源 | 不生成额外业务组；静态链依客户端能力配置。 |
| Intelligence、Telegram、YouTube、Google | 保留同名组 | 默认引用 Proxy。 |
| BiliBili、Emby | 保留同名组 | 默认 DIRECT；BiliBili 港澳台访问通过手动选节点而非地区组。 |

原配置的 `deepseek.com` 直接指定 Proxy，本次按新要求改为 Intelligence；`grok.com` 的公开规则落到 Intelligence，设备本地补入更高优先级的 `LOCAL_STATIC` 后才恢复原静态落地行为。参考包中的私人例外都是占位值，必须由用户在设备本机补入。

原配置没有启用公开 Emby 规则集：两个私人列表为注释。这里只将公开的 `emby.media` 映射到 Emby；自建媒体服务的私人域名和 IP 需要本地补充。

## 授权和规则损失

Sukka 规则使用 AGPL-3.0，blackmatrix7 规则使用 GPL-2.0，EAlyce 规则使用 MIT。缓存和输出按上游分别保存，保留来源和许可证文件。生成过程中不能表达的规则不会伪装成已迁移；每个客户端每个上游的计数保存在 `dist/BUILD_REPORT.json`。同一上游内的完全重复项会去重；跨来源的重叠按原顺序保留，因为不同出口的优先级可能不同。
