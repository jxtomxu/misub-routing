# MiSub 统一分流规则中心

本仓库把公开规则定义集中在 [`schema/routing.yaml`](schema/routing.yaml)，从 22 个已注明来源的公开规则集生成 Quantumult X、Mihomo、Shadowrocket 三套输出。MiSub 只提供节点；真实订阅地址、自建节点、落地链和私人规则留在设备本地。

**当前状态：测试版。** 三套输出各通过 21 项离线首条匹配检查；Mihomo 已在本机以测试节点启动并加载规则提供器。Quantumult X、Shadowrocket 和 FlClash 尚未实机导入或联网验收。私人 Snell、静态落地、私人域名与 IP 未从脱敏参考配置中恢复。请先读 [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md)，不要直接替换正在使用的生产配置。

只定义八个业务策略组：`Proxy`、`Intelligence`、`Telegram`、`YouTube`、`Google`、`BiliBili`、`GlobalMedia`、`Emby`。Shadowrocket 的节点自动纳入与 `Proxy` 中同时提供 `DIRECT` 有兼容限制，见兼容性文档。

- [四个客户端的安装方法](docs/SETUP.md)
- [架构与规则迁移](docs/ARCHITECTURE.md)
- [完整文件清单](docs/FILES.md)
- [更新与回滚](docs/UPDATE_GUIDE.md)
- [兼容性与未完成事项](docs/COMPATIBILITY.md)
- [故障排查](docs/TROUBLESHOOTING.md)
- [敏感信息扫描说明](docs/SECURITY_SCAN.md)
- [机器可读的构建报告](dist/BUILD_REPORT.json)

本仓库的上游缓存与转换文件分别保留来源，许可证见 [`LICENSES/`](LICENSES/)。更新器在任一上游下载失败、内容异常或构建失败时保留上一次有效版本。规则内容自动更新不等于配置结构和客户端兼容性永远无需调整，详见更新文档。
