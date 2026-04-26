/**
 * QuantaMind 桌面客户端 - Electron 主进程
 * 独立窗口应用，可打包为可安装的 .exe
 */

const { app, BrowserWindow, shell } = require('electron');
const fs = require('fs');
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

  const frontendUrl = process.env.QUANTAMIND_DESKTOP_FRONTEND_URL;
  if (frontendUrl) {
    mainWindow.loadURL(frontendUrl);
  } else {
    mainWindow.loadFile(resolveFrontendEntry());
  }

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });

  // 新窗口（如外链）用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function resolveFrontendEntry() {
  const packagedFrontend = path.join(process.resourcesPath, 'frontend-dist', 'index.html');
  const workspaceFrontend = path.join(__dirname, '..', 'frontend', 'dist', 'index.html');
  const fallbackFrontend = path.join(__dirname, 'ui', 'index.html');

  for (const candidate of [packagedFrontend, workspaceFrontend, fallbackFrontend]) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return fallbackFrontend;
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (mainWindow === null) createWindow(); });
