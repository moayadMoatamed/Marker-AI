"use client";

import { useState, useCallback, useRef, useEffect } from "react";

// ── Types ────────────────────────────────────────────────────────────────────

interface Concept {
  concept_id: string;
  technique_used: string;
  one_line_idea: string;
  the_trick: string;
  meaning_mapping: { element: string; represents: string; because: string }[];
  construction_recipe: string;
  monochrome_survives: boolean;
  sixteen_px_survives: boolean;
  closest_existing_logo: string;
  rationale_paragraph: string;
}

interface Score {
  concept_id: string;
  cleverness_score: number;
  specificity_score: number;
  monochrome_score: number;
  scalability_score: number;
  originality_score: number;
  emotional_fit_score: number;
  total: number;
  weakest_aspect: string;
  recommend: "ship" | "refine" | "reject";
  refinement_direction?: string | null;
}

interface RunStatus {
  run_id: string;
  stage: string;
  concepts: Concept[];
  images: Record<string, string>;
  scores: Score[];
  error: string | null;
}

const API_BASE = "";

// ── Helpers ──────────────────────────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  starting: "Starting...",
  deconstructing: "Extracting brand facts...",
  raw_material: "Mapping visual opportunities...",
  technique_search: "Evaluating design techniques...",
  synthesizing: "Generating logo concepts...",
  critiquing: "Scoring concepts...",
  complete: "Complete",
  error: "Error",
};

const STAGE_DOTS: Record<string, string> = {
  deconstructing: "bg-brand-400",
  raw_material: "bg-brand-500",
  technique_search: "bg-brand-600",
  synthesizing: "bg-accent-400",
  critiquing: "bg-accent-500",
  rendering: "bg-accent-600",
};

function scoreColor(total: number): string {
  if (total >= 45) return "text-emerald-600";
  if (total >= 30) return "text-amber-600";
  return "text-red-500";
}

function recBadge(rec: string): string {
  if (rec === "ship") return "bg-emerald-100 text-emerald-800 border-emerald-200";
  if (rec === "refine") return "bg-amber-100 text-amber-800 border-amber-200";
  return "bg-red-50 text-red-600 border-red-200";
}

// ── Components ───────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-brand-500"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function StageIndicator({ stage }: { stage: string }) {
  const stages = [
    "deconstructing",
    "raw_material",
    "technique_search",
    "synthesizing",
    "critiquing",
    "rendering",
  ];
  const currentIdx = stages.indexOf(stage);

  return (
    <div className="flex items-center gap-1.5">
      {stages.map((s, i) => (
        <div
          key={s}
          className={`h-1.5 rounded-full transition-all duration-500 ${
            i <= currentIdx
              ? (STAGE_DOTS[s] || "bg-brand-500") + " w-6"
              : "bg-brand-200 w-1.5"
          }`}
        />
      ))}
    </div>
  );
}

function ConceptCard({
  concept,
  score,
  imagePath,
  runId,
  pipelineStage,
}: {
  concept: Concept;
  score?: Score;
  imagePath?: string;
  runId: string;
  pipelineStage: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const imgSrc = imagePath
    ? `${API_BASE}/api/runs/${runId}/${imagePath}`
    : null;

  const isComplete = pipelineStage === "complete";

  return (
    <div className="group border border-brand-100 rounded-2xl bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300">
      {/* Image */}
      {imgSrc ? (
        <div className="aspect-[16/10] bg-brand-50 relative overflow-hidden border-b border-brand-100">
          <img
            src={imgSrc}
            alt={concept.one_line_idea}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
      ) : (
        <div className={`aspect-[16/10] relative overflow-hidden border-b border-brand-100 flex items-center justify-center ${
          isComplete
            ? "bg-gradient-to-br from-red-50 via-red-50/50 to-amber-50"
            : "bg-gradient-to-br from-brand-50 via-brand-100 to-accent-50"
        }`}>
          <div className="text-center space-y-2 px-6">
            <div className={`w-12 h-12 mx-auto rounded-xl flex items-center justify-center ${
              isComplete ? "bg-red-100/60" : "bg-brand-200/50"
            }`}>
              {isComplete ? (
                <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.53 16.122a3 3 0 00-5.78 1.128 2.25 2.25 0 01-2.4 2.245 4.5 4.5 0 008.4-2.245c0-.399-.078-.78-.22-1.128zm0 0a15.998 15.998 0 003.388-1.62m-5.043-.025a15.994 15.994 0 011.622-3.395m3.42 3.42a15.995 15.995 0 004.764-4.648l3.876-5.814a1.151 1.151 0 00-1.597-1.597L14.146 6.32a15.996 15.996 0 00-4.649 4.763m3.42 3.42a6.776 6.776 0 00-3.42-3.42" />
                </svg>
              )}
            </div>
            <p className={`text-xs font-medium ${
              isComplete ? "text-red-500" : "text-brand-300"
            }`}>
              {isComplete ? "Image generation failed — check API credits" : "Image pending"}
            </p>
          </div>
        </div>
      )}

      <div className="p-5 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold text-brand-900 leading-snug text-[15px]">
              {concept.one_line_idea}
            </h3>
            <p className="text-[11px] text-brand-400 mt-1 font-mono uppercase tracking-wide">
              {concept.technique_used.replace(/_/g, " ")} &middot;{" "}
              {concept.concept_id}
            </p>
          </div>
          {score && (
            <div className="flex flex-col items-end shrink-0">
              <span
                className={`text-lg font-bold font-mono ${scoreColor(score.total)}`}
              >
                {score.total}/60
              </span>
              <span
                className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold border ${recBadge(score.recommend)}`}
              >
                {score.recommend}
              </span>
            </div>
          )}
        </div>

        {/* The Trick */}
        <div className="bg-gradient-to-r from-brand-50 to-transparent border-l-[3px] border-brand-400 pl-3.5 py-2.5 rounded-r-lg">
          <p className="text-sm text-brand-700 leading-relaxed">
            <span className="font-semibold text-brand-500 text-xs uppercase tracking-wide">
              The trick
            </span>
            <br />
            {concept.the_trick}
          </p>
        </div>

        {/* Meaning chips */}
        {!expanded && (
          <div className="flex flex-wrap gap-1.5">
            {concept.meaning_mapping.slice(0, 3).map((m, i) => (
              <span
                key={i}
                className="text-[11px] px-2.5 py-1 bg-brand-50 text-brand-600 rounded-md font-medium border border-brand-100"
              >
                {m.element} &rarr; {m.represents}
              </span>
            ))}
          </div>
        )}

        {/* Expanded detail */}
        {expanded && (
          <div className="space-y-4 pt-3 border-t border-brand-100">
            {/* Meaning mapping */}
            <div>
              <h4 className="text-[11px] font-semibold text-brand-400 uppercase tracking-wider mb-2">
                Meaning Mapping
              </h4>
              <ul className="space-y-1.5">
                {concept.meaning_mapping.map((m, i) => (
                  <li key={i} className="text-sm text-brand-700 flex gap-1.5">
                    <span className="shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full bg-accent-400" />
                    <span>
                      <span className="font-semibold">{m.element}</span>{" "}
                      &rarr; <span className="font-semibold">{m.represents}</span>
                      <span className="text-brand-500 block text-xs mt-0.5">
                        {m.because}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Construction recipe */}
            <div>
              <h4 className="text-[11px] font-semibold text-brand-400 uppercase tracking-wider mb-2">
                Construction Recipe
              </h4>
              <p className="text-sm text-brand-700 bg-brand-50 rounded-lg p-3 leading-relaxed whitespace-pre-line">
                {concept.construction_recipe}
              </p>
            </div>

            {/* Tests */}
            <div className="flex gap-3">
              <span
                className={`text-xs px-3 py-1.5 rounded-md font-medium border ${
                  concept.monochrome_survives
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-red-50 text-red-500 border-red-200"
                }`}
              >
                {concept.monochrome_survives ? "Mono survives" : "Mono fails"}
              </span>
              <span
                className={`text-xs px-3 py-1.5 rounded-md font-medium border ${
                  concept.sixteen_px_survives
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-red-50 text-red-500 border-red-200"
                }`}
              >
                {concept.sixteen_px_survives ? "16px survives" : "16px fails"}
              </span>
            </div>

            {/* Closest existing */}
            <p className="text-xs text-brand-400 italic">
              Closest existing logo: {concept.closest_existing_logo}
            </p>

            {/* Rationale */}
            <div>
              <h4 className="text-[11px] font-semibold text-brand-400 uppercase tracking-wider mb-2">
                Rationale
              </h4>
              <p className="text-sm text-brand-700 leading-relaxed">
                {concept.rationale_paragraph}
              </p>
            </div>

            {/* Score breakdown */}
            {score && (
              <div>
                <h4 className="text-[11px] font-semibold text-brand-400 uppercase tracking-wider mb-2">
                  Score Breakdown
                </h4>
                <div className="grid grid-cols-3 gap-1.5 text-xs">
                  {[
                    ["Cleverness", score.cleverness_score],
                    ["Specificity", score.specificity_score],
                    ["Monochrome", score.monochrome_score],
                    ["Scalability", score.scalability_score],
                    ["Originality", score.originality_score],
                    ["Emotional Fit", score.emotional_fit_score],
                  ].map(([label, val]) => (
                    <div
                      key={label}
                      className="flex justify-between bg-brand-50 px-2.5 py-2 rounded-lg"
                    >
                      <span className="text-brand-500">{label}</span>
                      <span className="font-mono font-semibold text-brand-800">
                        {val}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-brand-500 mt-2">
                  <span className="font-medium">Weakest: </span>
                  {score.weakest_aspect}
                </p>
                {score.refinement_direction && (
                  <p className="text-xs text-amber-700 mt-1 bg-amber-50 rounded-lg p-2">
                    <span className="font-medium">Refine: </span>
                    {score.refinement_direction}
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs font-semibold text-brand-400 hover:text-brand-600 transition-colors tracking-wide uppercase"
        >
          {expanded ? "Collapse ↑" : "Details ↓"}
        </button>
      </div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Home() {
  const [brandName, setBrandName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = useCallback((runId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/run/${runId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: RunStatus = await res.json();
        setStatus(data);

        // Keep polling through critiquing/rendering so images arrive
        const terminal = ["complete", "error"].includes(data.stage);
        if (terminal) {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setLoading(false);
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 1500);
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!brandName.trim() || description.trim().length < 20) return;

      setLoading(true);
      setError(null);
      setStatus(null);

      try {
        const res = await fetch(`${API_BASE}/api/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            brand_name: brandName.trim(),
            description: description.trim(),
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const { run_id } = await res.json();
        startPolling(run_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setLoading(false);
      }
    },
    [brandName, description, startPolling]
  );

  const stageLabel = status
    ? STAGE_LABELS[status.stage] || status.stage
    : null;
  const isRunning = loading || (status && status.stage !== "complete" && status.stage !== "error");

  return (
    <div className="relative z-[1] min-h-screen">
      <main className="max-w-5xl mx-auto px-5 py-16 space-y-12">
        {/* Header */}
        <header className="space-y-4 text-center">
          <div className="inline-flex items-center gap-2.5 bg-white border border-brand-200 rounded-full px-4 py-1.5 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-accent-500 animate-pulse" />
            <span className="text-[11px] font-semibold text-brand-500 uppercase tracking-widest">
              Concept Pipeline
            </span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-brand-900">
            Marker AI
          </h1>
          <p className="text-brand-500 max-w-lg mx-auto leading-relaxed">
            Conceptual logo generation powered by typographic analysis. Describe
            your brand and the system produces concept candidates with meaning
            mapping, critique scores, and construction recipes.
          </p>
        </header>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="space-y-5 max-w-xl mx-auto bg-white border border-brand-200 rounded-2xl p-6 shadow-sm"
        >
          <div>
            <label
              htmlFor="brandName"
              className="block text-xs font-semibold text-brand-500 uppercase tracking-wider mb-2"
            >
              Brand name
            </label>
            <input
              id="brandName"
              type="text"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              required
              placeholder="e.g. Morning Node"
              className="w-full border border-brand-200 rounded-xl px-4 py-3 text-sm
                         focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400
                         placeholder:text-brand-300 transition-all bg-brand-50/50"
            />
          </div>
          <div>
            <label
              htmlFor="description"
              className="block text-xs font-semibold text-brand-500 uppercase tracking-wider mb-2"
            >
              What does your company do?
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              minLength={20}
              rows={4}
              placeholder="Describe what you do, who you serve, where the name comes from, and any visual preferences or constraints..."
              className="w-full border border-brand-200 rounded-xl px-4 py-3 text-sm
                         focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400
                         placeholder:text-brand-300 transition-all bg-brand-50/50 resize-y"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-brand-900 text-white font-semibold rounded-xl
                       hover:bg-brand-800 active:bg-brand-950
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-all text-sm shadow-lg shadow-brand-900/10
                       hover:shadow-brand-900/20"
          >
            {loading ? "Generating..." : "Generate Concepts"}
          </button>
          {error && (
            <p className="text-red-600 text-sm text-center bg-red-50 rounded-lg py-2">
              {error}
            </p>
          )}
        </form>

        {/* Status */}
        {isRunning && stageLabel && (
          <div className="flex flex-col items-center justify-center gap-3">
            <div className="flex items-center gap-2.5 text-brand-600 bg-white border border-brand-200 rounded-full px-5 py-2.5 shadow-sm">
              <Spinner />
              <span className="text-sm font-medium">{stageLabel}</span>
            </div>
            {status && <StageIndicator stage={status.stage} />}
          </div>
        )}

        {status?.error && (
          <div className="max-w-xl mx-auto bg-red-50 border border-red-200 rounded-2xl p-5">
            <p className="text-red-700 text-sm font-semibold">Pipeline Error</p>
            <p className="text-red-600 text-sm mt-1">{status.error}</p>
          </div>
        )}

        {/* Results */}
        {status?.concepts && status.concepts.length > 0 && (
          <section className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-brand-900">
                Concepts{" "}
                <span className="text-brand-400 font-medium">
                  ({status.concepts.length})
                </span>
              </h2>
            </div>
            <div className="grid gap-5 md:grid-cols-2">
              {status.concepts.map((concept) => {
                const score = status.scores?.find(
                  (s) => s.concept_id === concept.concept_id
                );
                const imageKey = Object.keys(status.images || {}).find((k) =>
                  k.includes(concept.concept_id)
                );
                return (
                  <ConceptCard
                    key={concept.concept_id}
                    concept={concept}
                    score={score}
                    imagePath={
                      imageKey || status.images?.[concept.concept_id]
                    }
                    runId={status.run_id}
                    pipelineStage={status.stage}
                  />
                );
              })}
            </div>
          </section>
        )}

        {/* Empty state */}
        {!status && !loading && (
          <div className="text-center space-y-3 pt-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-100 mb-2">
              <svg
                className="w-7 h-7 text-brand-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
                />
              </svg>
            </div>
            <p className="text-brand-500 text-sm font-medium">
              Enter your brand details above to get started
            </p>
            <p className="text-brand-300 text-xs max-w-md mx-auto">
              The pipeline extracts brand facts, maps visual opportunities,
              evaluates design techniques, synthesizes concepts, and critiques
              the results.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
