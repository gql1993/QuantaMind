# QuantaMind 桌面客户端（可安装软件）

基于 Electron 的**可安装桌面应用**，安装后从开始菜单或桌面快捷方式打开，无需浏览器。

## 开发 / 直接运行

1. 安装依赖（需 Node.js）：

   ```bash
   cd E:\work\QuantaMind\desktop
   npm install
   ```

2. 启动 QuantaMind 服务端（若未启动）：

   ```bash
   cd E:\work\QuantaMind
   python run_gateway.py
   ```

3. 启动桌面客户端：

   ```bash
   npm start
   ```

## 打包成可安装程序（.exe 安装包）

```bash
cd E:\work\QuantaMind\desktop
npm run dist
```

完成后在 `desktop/dist/` 下会生成安装程序（如 `QuantaMind Setup 1.0.0.exe`），双击安装即可在桌面/开始菜单使用「QuantaMind」。

安装后首次使用前，需先启动 QuantaMind 服务端（`python run_gateway.py`），或使用「QuantaMind Client」快捷方式（会先自动启动服务端再开窗口）。
