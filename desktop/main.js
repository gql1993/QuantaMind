/**
 * QuantaMind 桌面客户端 - Electron 主进程
 * 独立窗口应用，可打包为可安装的 .exe
 */

const { app, BrowserWindow, shell } = require('electron');
const path = require('path');

const GATEWAY_PORT = process.env.QUANTAMIND_GATEWAY_PORT || '18789';
const GATEWAY_URL = `http://127.0.0.1:${GATEWAY_PORT}`;

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    minWidth: 500,
    minHeight: 400,
    title: 'QuantaMind 客户端',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      // 允许页面 fetch 本地 Gateway（否则 file:// 下 CORS 会拦）
      webSecurity: false,
    },
    show: false,
  });

  const indexPath = path.join(__dirname, 'ui', 'index.html');
  mainWindow.loadFile(indexPath);

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });

  // 新窗口（如外链）用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (mainWindow === null) createWindow(); });
