import { app, BrowserWindow } from 'electron'
import path from 'path'
import { startSidecar, stopSidecar } from './sidecar'

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  try {
    await startSidecar()
  } catch (err) {
    console.error('Sidecar start failed, continuing without it:', err)
  }
  createWindow()
})

app.on('window-all-closed', () => {
  stopSidecar()
  app.quit()
})

app.on('before-quit', () => {
  stopSidecar()
})
