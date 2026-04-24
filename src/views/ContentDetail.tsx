import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ContentItem, JobDetail, RepurposeResponse } from "../api/types";

const FORMATS = [
  { id: "linkedin", label: "LinkedIn Post" },
  { id: "email", label: "Email" },
  { id: "twitter", label: "Twitter Thread" },
  { id: "summary", label: "Summary" },
];
const TONES = ["professional", "casual", "technical", "friendly"];

export default function ContentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [content, setContent] = useState<ContentItem | null>(null);
  const [similar, setSimilar] = useState<ContentItem[]>([]);
  const [error, setError] = useState("");
  const [selectedFormats, setSelectedFormats] = useState<string[]>([
    "linkedin",
  ]);
  const [tone, setTone] = useState("professional");
  const [repurposeResult, setRepurposeResult] =
    useState<RepurposeResponse | null>(null);
  const [activeJob, setActiveJob] = useState<JobDetail | null>(null);
  const [repurposing, setRepurposing] = useState(false);
  const [activeTab, setActiveTab] = useState("");

  useEffect(() => {
    if (!id) return;
    api
      .getContent(id)
      .then(setContent)
      .catch(() => setError("Content not found"));
    api
      .getSimilar(id)
      .then(setSimilar)
      .catch(() => {});
  }, [id]);

  useEffect(() => {
    if (
      !activeJob ||
      activeJob.status === "succeeded" ||
      activeJob.status === "failed"
    ) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const next = await api.getJob(activeJob.id);
        setActiveJob(next);
        if (next.status === "succeeded" && next.result) {
          const result = next.result as unknown as RepurposeResponse;
          setRepurposeResult(result);
          setActiveTab(Object.keys(result.generated_content ?? {})[0] || "");
          setRepurposing(false);
        } else if (next.status === "failed") {
          setRepurposing(false);
          setError(next.error || "Repurpose job failed");
        }
      } catch (err: unknown) {
        setRepurposing(false);
        setError(err instanceof Error ? err.message : String(err));
      }
    }, 1500);

    return () => window.clearInterval(interval);
  }, [activeJob]);

  async function handleRepurpose() {
    if (!id || selectedFormats.length === 0) return;
    setRepurposing(true);
    setRepurposeResult(null);
    setActiveJob(null);
    setError("");
    try {
      const job = await api.createRepurposeJob({
        content_id: id,
        formats: selectedFormats,
        tone,
      });
      setActiveJob(job);
      if (job.status === "succeeded" && job.result) {
        const result = job.result as unknown as RepurposeResponse;
        setRepurposeResult(result);
        setActiveTab(Object.keys(result.generated_content ?? {})[0] || "");
        setRepurposing(false);
      } else if (job.status === "failed") {
        setError(job.error || "Repurpose job failed");
        setRepurposing(false);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      setRepurposing(false);
    }
  }

  if (error && !content)
    return <div className="text-center py-8 text-red-500">{error}</div>;
  if (!content)
    return (
      <div className="text-center py-8 text-muted-foreground">Loading...</div>
    );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 lg:flex-row lg:items-start lg:gap-10">
      <div className="min-w-0 flex-1 space-y-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-0 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back
        </button>

        <article className="max-w-[65ch] space-y-4">
          <h1 className="text-balance text-2xl font-semibold tracking-tight">
            {content.title}
          </h1>
          <div className="flex flex-wrap gap-2">
            <Tag>{content.content_type}</Tag>
            <Tag>{content.persona}</Tag>
            <Tag>{content.funnel_stage}</Tag>
            {content.performance_score > 0 && (
              <Tag>{content.performance_score}%</Tag>
            )}
          </div>
          {content.summary && (
            <p className="text-sm italic leading-relaxed text-muted-foreground">
              {content.summary}
            </p>
          )}
          <div className="rounded-lg border border-border/80 bg-muted/10 px-4 py-4 sm:px-5 sm:py-5">
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
              {content.body}
            </div>
          </div>
        </article>

        {activeJob && (
          <div className="max-w-[65ch] rounded-lg border border-border bg-muted/20 p-4">
            <p className="text-sm font-medium">Repurpose Job</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Status:{" "}
              <span className="font-medium text-foreground">
                {activeJob.status}
              </span>
            </p>
            {activeJob.error && (
              <p className="mt-2 text-xs text-red-500">{activeJob.error}</p>
            )}
          </div>
        )}

        {repurposeResult && repurposeResult.success && (
          <div className="max-w-none space-y-4 border-t border-border pt-8">
            <h2 className="text-lg font-semibold">Generated Content</h2>
            <div className="flex flex-wrap gap-2">
              {Object.keys(repurposeResult.generated_content).map((fmt) => (
                <button
                  type="button"
                  key={fmt}
                  onClick={() => setActiveTab(fmt)}
                  className={`rounded-md px-3 py-1.5 text-sm ${activeTab === fmt ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"}`}
                >
                  {fmt}
                  {repurposeResult.quality_scores[fmt] != null && (
                    <span className="ml-1 opacity-70">
                      ({Math.round(repurposeResult.quality_scores[fmt] * 100)}%)
                    </span>
                  )}
                </button>
              ))}
            </div>
            {activeTab && repurposeResult.generated_content[activeTab] && (
              <div className="rounded-lg border border-border bg-muted/20 p-4 sm:p-5">
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                  {repurposeResult.generated_content[activeTab]}
                </pre>
              </div>
            )}
          </div>
        )}
        {repurposeResult && !repurposeResult.success && (
          <div className="text-sm text-red-500">
            Errors: {repurposeResult.errors.join(", ")}
          </div>
        )}
      </div>

      <aside className="w-full shrink-0 space-y-6 lg:w-80 lg:sticky lg:top-6 lg:self-start">
        <div className="rounded-lg border border-border p-4 sm:p-5">
          <h3 className="mb-3 font-semibold">Repurpose Content</h3>
          <div className="mb-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Formats
            </p>
            {FORMATS.map((f) => (
              <label
                key={f.id}
                className="flex items-center gap-2 text-sm mb-1"
              >
                <input
                  type="checkbox"
                  checked={selectedFormats.includes(f.id)}
                  onChange={(e) =>
                    setSelectedFormats(
                      e.target.checked
                        ? [...selectedFormats, f.id]
                        : selectedFormats.filter((x) => x !== f.id),
                    )
                  }
                />
                {f.label}
              </label>
            ))}
          </div>
          <div className="mb-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Tone
            </p>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
            >
              {TONES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={handleRepurpose}
            disabled={repurposing || selectedFormats.length === 0}
            className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {repurposing ? "Queueing..." : "Generate"}
          </button>
        </div>
        {similar.length > 0 && (
          <div className="rounded-lg border border-border p-4 sm:p-5">
            <h3 className="mb-3 text-sm font-semibold">Similar Content</h3>
            <ul className="space-y-1">
              {similar.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => navigate(`/content/${s.id}`)}
                    className="w-full rounded-md px-2 py-1.5 text-left text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <span className="line-clamp-2">{s.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </div>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
      {children}
    </span>
  );
}
