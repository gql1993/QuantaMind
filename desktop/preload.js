/**
 * 预加载脚本：向页面暴露 Gateway 地址
 */
const { contextBridge } = require('electron');

const port = process.env.QUANTAMIND_GATEWAY_PORT || '18789';
contextBridge.exposeInMainWorld('electronAPI', {
  gatewayUrl: `http://127.0.0.1:${port}`,
});
