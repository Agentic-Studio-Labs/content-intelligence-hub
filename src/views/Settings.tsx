import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { AppSettings, IntegrationState, JobDetail } from "../api/types";

export default function Settings() {
  const backend = useMemo(() => api.backendInfo(), []);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [integrations, setIntegrations] = useState<IntegrationState[]>([]);
  const [ingestJob, setIngestJob] = useState<JobDetail | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [newFolder, setNewFolder] = useState("");
  const [folders, setFolders] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        setSettings(s);
        setFolders(s.watched_folders ?? []);
      })
      .catch((e) => setError(e.message));

    if (backend.mode === "cloud") {
      api
        .listIntegrations()
        .then(setIntegrations)
        .catch((e) => setError(e.message));
    }
  }, [backend.mode]);

  useEffect(() => {
    if (
      !ingestJob ||
      ingestJob.status === "succeeded" ||
      ingestJob.status === "failed"
    ) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const next = await api.getJob(ingestJob.id);
        setIngestJob(next);
        if (next.status === "succeeded") {
          setMessage(
            `Ingested ${(next.result as { ingested?: number } | null)?.ingested ?? 0} file(s).`,
          );
          setUploading(false);
        } else if (next.status === "failed") {
          setError(next.error || "Ingest job failed");
          setUploading(false);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : String(err));
        setUploading(false);
      }
    }, 1500);

    return () => window.clearInterval(interval);
  }, [ingestJob]);

  async function saveApiKey() {
    try {
      await api.updateSettings({ anthropic_api_key: apiKey });
      setApiKey("");
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      const s = await api.getSettings();
      setSettings(s);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function addFolder() {
    if (!newFolder.trim()) return;
    const updated = [...folders, newFolder.trim()];
    try {
      await api.updateSettings({ watched_folders: updated });
      setFolders(updated);
      setNewFolder("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function removeFolder(path: string) {
    const updated = folders.filter((f) => f !== path);
    try {
      await api.updateSettings({ watched_folders: updated });
      setFolders(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function ingestFolder(path: string) {
    try {
      const result = await api.ingest([path]);
      alert(`Ingested ${result.ingested} files from ${path}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function uploadAndQueueIngest() {
    if (files.length === 0) return;
    setUploading(true);
    setMessage("");
    setError("");
    try {
      const objectPaths = [];
      for (const file of files) {
        objectPaths.push(await api.uploadFile(file));
      }
      const job = await api.createIngestJob({
        object_paths: objectPaths,
        source_label: "desktop-upload",
      });
      setIngestJob(job);
      if (job.status === "succeeded") {
        setMessage(
          `Ingested ${(job.result as { ingested?: number } | null)?.ingested ?? 0} file(s).`,
        );
        setUploading(false);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setUploading(false);
    }
  }

  if (!settings)
    return (
      <div className="text-center py-8 text-muted-foreground">
        Loading settings...
      </div>
    );

  if (backend.mode === "cloud") {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-2">
            Cloud control-plane configuration for the operator desktop.
          </p>
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        {message && <p className="text-emerald-600 text-sm">{message}</p>}

        <section className="border border-border rounded-lg p-5">
          <h2 className="font-semibold mb-3">Workspace</h2>
          <dl className="grid grid-cols-2 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Backend Mode</dt>
            <dd>{backend.mode}</dd>
            <dt className="text-muted-foreground">Base URL</dt>
            <dd className="font-mono text-xs">{backend.baseUrl}</dd>
            <dt className="text-muted-foreground">Auth Mode</dt>
            <dd>{settings.auth_mode ?? "magic_link"}</dd>
            <dt className="text-muted-foreground">Workspace</dt>
            <dd>{settings.workspace_name ?? "Default Workspace"}</dd>
            <dt className="text-muted-foreground">Upload Mode</dt>
            <dd>{settings.upload_mode ?? "cloud"}</dd>
          </dl>
        </section>

        <section className="border border-border rounded-lg p-5">
          <h2 className="font-semibold mb-3">Integrations</h2>
          <div className="grid gap-3">
            {integrations.map((integration) => (
              <div
                key={integration.id}
                className="rounded-md border border-border p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium capitalize">
                      {integration.provider}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {integration.status_message || "No status reported"}
                    </p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${integration.connected ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}
                  >
                    {integration.connected ? "Connected" : "Pending"}
                  </span>
                </div>
                {(integration.last_checked_at ||
                  integration.last_rotated_at) && (
                  <div className="text-xs text-muted-foreground mt-3 space-y-1">
                    {integration.last_checked_at && (
                      <p>
                        Last checked:{" "}
                        {new Date(integration.last_checked_at).toLocaleString()}
                      </p>
                    )}
                    {integration.last_rotated_at && (
                      <p>
                        Last rotated:{" "}
                        {new Date(integration.last_rotated_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
            {integrations.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No integration state available yet.
              </p>
            )}
          </div>
        </section>

        <section className="border border-border rounded-lg p-5">
          <h2 className="font-semibold mb-3">Upload And Ingest</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Upload source files into cloud storage, then queue an ingest job
            that creates cloud-owned content records.
          </p>
          <input
            type="file"
            multiple
            accept=".md,.markdown,.txt,.pdf,.docx"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className="block w-full text-sm"
          />
          {files.length > 0 && (
            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              {files.map((file) => (
                <li key={file.name}>{file.name}</li>
              ))}
            </ul>
          )}
          <button
            onClick={() => void uploadAndQueueIngest()}
            disabled={uploading || files.length === 0}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload And Queue Ingest"}
          </button>
          {ingestJob && (
            <div className="mt-4 rounded-md border border-border bg-muted/20 p-4 text-sm">
              <p className="font-medium">Ingest Job</p>
              <p className="text-muted-foreground mt-1">
                Status: {ingestJob.status}
              </p>
              {ingestJob.error && (
                <p className="text-red-500 mt-2">{ingestJob.error}</p>
              )}
            </div>
          )}
        </section>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-semibold">Settings</h1>
      {error && <p className="text-red-500 text-sm">{error}</p>}

      <section className="border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-1">Anthropic API Key</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Required for content repurposing and AI-powered search.
          {settings.anthropic_api_key_set && (
            <span className="text-green-600 ml-2">Configured</span>
          )}
        </p>
        <div className="flex gap-2">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={
              settings.anthropic_api_key_set ? "********" : "sk-ant-..."
            }
            className="flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          <button
            onClick={saveApiKey}
            disabled={!apiKey}
            className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {saved ? "Saved!" : "Save"}
          </button>
        </div>
      </section>

      <section className="border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-1">Watched Folders</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Content from these folders will be automatically imported.
        </p>
        {folders.length > 0 && (
          <ul className="space-y-2 mb-3">
            {folders.map((f) => (
              <li
                key={f}
                className="flex items-center justify-between text-sm border border-border rounded-md px-3 py-2"
              >
                <span className="font-mono text-xs truncate flex-1">{f}</span>
                <div className="flex gap-2 ml-2">
                  <button
                    onClick={() => ingestFolder(f)}
                    className="text-xs text-primary hover:underline"
                  >
                    Import Now
                  </button>
                  <button
                    onClick={() => removeFolder(f)}
                    className="text-xs text-red-500 hover:underline"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={newFolder}
            onChange={(e) => setNewFolder(e.target.value)}
            placeholder="/path/to/content/folder"
            className="flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          <button
            onClick={addFolder}
            disabled={!newFolder.trim()}
            className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </section>

      <section className="border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-2">System Info</h2>
        <dl className="grid grid-cols-2 gap-y-1 text-sm">
          <dt className="text-muted-foreground">LLM Model</dt>
          <dd>{settings.llm_model}</dd>
          <dt className="text-muted-foreground">Embedding Model</dt>
          <dd>{settings.embedding_model}</dd>
        </dl>
      </section>
    </div>
  );
}
