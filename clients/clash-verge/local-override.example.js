// 复制到 Clash Verge 本机脚本覆写，再填写；不要把实际值写入 GitHub 仓库。
function main(config) {
  const subscriptionUrl = ""; // 在本机粘贴 MiSub 的 Mihomo 节点订阅地址
  const snell = null; // 本机填写名为 LOCAL_SNELL 的真实 Mihomo 节点对象
  const staticLanding = null; // 本机填写名为 LOCAL_STATIC 的真实落地节点对象，可使用 dialer-proxy
  const privateRules = []; // 本机填写私有例外，如 DOMAIN-SUFFIX,<private>,DIRECT
  if (!subscriptionUrl || !snell || !staticLanding) {
    throw new Error("请在本机填写 MiSub、LOCAL_SNELL 和 LOCAL_STATIC；不得上传凭据");
  }
  config["proxy-providers"].MiSub.url = subscriptionUrl;
  config.proxies = [...(config.proxies || []), snell, staticLanding];
  config.rules = [...privateRules, "DOMAIN-SUFFIX,grok.com,LOCAL_STATIC", ...config.rules];
  return config;
}
