const { app, BrowserWindow } = require('electron')
const path = require('path')
require('@electron/remote/main').initialize()

function createWindow () {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        }
    })

    require('@electron/remote/main').enable(win.webContents)
    
    win.loadFile('Frontend/Templates/EyesTracking/index.html')
    win.webContents.openDevTools()
}

app.whenReady().then(() => {
    createWindow()
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})