const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')
require('@electron/remote/main').initialize()

let pythonProcess = null
let mainWindow = null

function checkServerStatus(url) {
    return new Promise((resolve, reject) => {
        http.get(url, (res) => {
            if (res.statusCode === 200) {
                resolve(true)
            } else {
                reject(new Error(`Server returned status code: ${res.statusCode}`))
            }
        }).on('error', (err) => {
            reject(err)
        })
    })
}

function startPythonServer() {
    return new Promise((resolve) => {
        console.log('Iniciando servidor Python...')

        const scriptPath = path.join(__dirname, 'Backend', 'BackendAdministrator.py')
        console.log('Starting Python script at:', scriptPath)

        pythonProcess = spawn('python', [scriptPath], {
            stdio: 'inherit'
        })

        pythonProcess.on('error', (err) => {
            console.error('Error al iniciar Python:', err)
        })

        pythonProcess.on('close', (code) => {
            console.log(`Servidor Python cerrado con código ${code}`)
        })

        // Give Python some time to initialize
        setTimeout(resolve, 5000)
    })
}

async function waitForServer(url, maxAttempts = 30) {  // Increased max attempts
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            await checkServerStatus(url)
            console.log('Server is ready!')
            return true
        } catch (err) {
            console.log(`Attempt ${attempt + 1}/${maxAttempts}: Server not ready yet...`)
            console.log('Error:', err.message)
            await new Promise(resolve => setTimeout(resolve, 1000))
        }
    }
    throw new Error('Server failed to start after maximum attempts')
}

async function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
            webSecurity: false // Solo para desarrollo
        }
    })

    require('@electron/remote/main').enable(mainWindow.webContents)

    mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
        callback({
            responseHeaders: {
                ...details.responseHeaders,
                'Content-Security-Policy': ['default-src \'self\' \'unsafe-inline\' \'unsafe-eval\' http://localhost:8000 ws://localhost:8000 ws://127.0.0.1:8000']  // Added ws://127.0.0.1:8000
            }
        })
    })

    try {
        // Try to connect to the server
        // let url_to_connect = 'http://localhost:8000/Templates/EyesTracking/index.html';
        let url_to_connect = 'http://127.0.0.1:8000/Templates/EyesTracking/index.html';
        await waitForServer(url_to_connect);

        // Once server is ready, load the URL
        // const url = 'http://127.0.0.1:8000/Templates/EyesTracking/index.html'
        console.log('Loading URL:', url_to_connect)

        // Add an additional small delay before loading the URL
        await new Promise(resolve => setTimeout(resolve, 1000))

        await mainWindow.loadURL(url_to_connect)
        mainWindow.webContents.openDevTools()
    } catch (error) {
        console.error('Failed to load application:', error)
        await mainWindow.loadURL(`data:text/html,
            <html>
                <body>
                    <h2>Failed to start application</h2>
                    <pre>${error.message}</pre>
                    <p>Please check if:</p>
                    <ul>
                        <li>Python is installed and in PATH</li>
                        <li>All required Python packages are installed</li>
                        <li>The server script path is correct</li>
                    </ul>
                </body>
            </html>
        `)
    }
}

app.whenReady().then(async () => {
    // First start Python and wait for initial setup
    await startPythonServer()

    // Then create the window
    await createWindow()
})

app.on('window-all-closed', () => {
    if (pythonProcess) {
        eel.stop_data_collection()();
        pythonProcess.kill()
    }
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('quit', () => {
    if (pythonProcess) {
        eel.stop_data_collection()();
        pythonProcess.kill()
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
    }
})