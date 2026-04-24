import { spawn, ChildProcess } from "child_process";
import path from "path";
import { app } from "electron";
import http from "http";

const SIDECAR_PORT = 8420;
const HEALTH_URL = `http://localhost:${SIDECAR_PORT}/health`;
const MAX_RETRIES = 30;
const RETRY_INTERVAL_MS = 500;

let sidecarProcess: ChildProcess | null = null;

function shouldStartLocalSidecar(): boolean {
  if (process.env.CIH_USE_LOCAL_SIDECAR === "false") {
    return false;
  }

  const apiBaseUrl = process.env.CIH_API_BASE_URL?.trim();
  if (!apiBaseUrl) {
    return true;
  }

  return (
    apiBaseUrl.includes("localhost:8420") ||
    apiBaseUrl.includes("127.0.0.1:8420")
  );
}

export function startSidecar(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!shouldStartLocalSidecar()) {
      console.log(
        "Skipping local sidecar startup because cloud API mode is enabled",
      );
      resolve();
      return;
    }

    const isDev = !app.isPackaged;
    const sidecarDir = isDev
      ? path.join(app.getAppPath(), "sidecar")
      : path.join(process.resourcesPath, "sidecar");

    const pythonPath = isDev
      ? path.join(sidecarDir, ".venv", "bin", "python")
      : path.join(sidecarDir, "python", "bin", "python3");

    console.log(`Starting sidecar from ${sidecarDir}`);

    sidecarProcess = spawn(
      pythonPath,
      [
        "-m",
        "uvicorn",
        "api:app",
        "--port",
        String(SIDECAR_PORT),
        "--host",
        "127.0.0.1",
      ],
      {
        cwd: sidecarDir,
        stdio: ["ignore", "pipe", "pipe"],
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
      },
    );

    sidecarProcess.stdout?.on("data", (data) => {
      console.log(`[sidecar] ${data.toString().trim()}`);
    });

    sidecarProcess.stderr?.on("data", (data) => {
      console.error(`[sidecar] ${data.toString().trim()}`);
    });

    sidecarProcess.on("error", (err) => {
      console.error("Failed to start sidecar:", err);
      reject(err);
    });

    sidecarProcess.on("exit", (code) => {
      console.log(`Sidecar exited with code ${code}`);
      sidecarProcess = null;
    });

    waitForHealth(0, resolve, reject);
  });
}

function waitForHealth(
  attempt: number,
  resolve: () => void,
  reject: (err: Error) => void,
): void {
  if (attempt >= MAX_RETRIES) {
    reject(new Error("Sidecar failed to start"));
    return;
  }
  setTimeout(() => {
    http
      .get(HEALTH_URL, (res) => {
        if (res.statusCode === 200) {
          console.log("Sidecar is ready");
          resolve();
        } else {
          waitForHealth(attempt + 1, resolve, reject);
        }
      })
      .on("error", () => {
        waitForHealth(attempt + 1, resolve, reject);
      });
  }, RETRY_INTERVAL_MS);
}

export function stopSidecar(): void {
  if (sidecarProcess) {
    console.log("Stopping sidecar...");
    sidecarProcess.kill("SIGTERM");
    sidecarProcess = null;
  }
}
