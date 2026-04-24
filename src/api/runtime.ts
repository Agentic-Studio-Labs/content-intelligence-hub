import type { BackendInfo } from "./types";

const rawBaseUrl = (
  import.meta.env.VITE_API_BASE_URL as string | undefined
)?.trim();
export const API_BASE_URL = (rawBaseUrl || "http://localhost:8420").replace(
  /\/$/,
  "",
);
export const API_AUTH_REQUIRED =
  (import.meta.env.VITE_REQUIRE_AUTH as string | undefined) === "true";
export const API_MODE = (
  (import.meta.env.VITE_API_MODE as string | undefined) === "cloud"
    ? "cloud"
    : "local"
) as BackendInfo["mode"];

export function getBackendInfo(): BackendInfo {
  return {
    mode: API_MODE,
    baseUrl: API_BASE_URL,
    authRequired: API_AUTH_REQUIRED,
  };
}
