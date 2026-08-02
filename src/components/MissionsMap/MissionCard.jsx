// MissionCard.jsx — redesign complet
import MissionTimeline from "./MissionTimeline.jsx";

const STATUS = {
  planned:     { label: "Planifiée",  stripe: "bg-[var(--text-3)]",  badge: "bg-surface-hover text-tertiary border-border/60" },
  in_progress: { label: "En cours",   stripe: "bg-cyan",              badge: "bg-cyan/10 text-cyan border-cyan/20" },
  completed:   { label: "Terminée",   stripe: "bg-brand-light",       badge: "bg-brand/10 text-brand-light border-brand/20" },
  cancelled:   { label: "Annulée",    stripe: "bg-danger",            badge: "bg-danger/10 text-danger-text border-danger/25" },
};

const IcoPackage = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M3.5 8l8.5-4.5L20.5 8v8L12 20.5 3.5 16V8z" /><path strokeLinecap="round" strokeLinejoin="round" d="M3.5 8L12 12.5 20.5 8M12 12.5V20.5" /></svg>;
const IcoRoute   = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><circle cx="6" cy="6" r="2" /><circle cx="18" cy="18" r="2" /><path strokeLinecap="round" d="M6 8v3a4 4 0 004 4h4a4 4 0 004 4" strokeDasharray="2 3" /></svg>;
const IcoClock   = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><circle cx="12" cy="12" r="8.5" /><path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5V12l3 2" /></svg>;
const IcoTruck   = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><rect x="2.5" y="7" width="11" height="9" rx="1.2" /><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10h4l3 3v3h-7v-6z" /><circle cx="6.5" cy="17.5" r="1.6" /><circle cx="16.5" cy="17.5" r="1.6" /></svg>;
const IcoPin     = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M12 21s-7-6.2-7-11a7 7 0 1114 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.4" /></svg>;
const IcoPlay    = (p) => <svg viewBox="0 0 24 24" fill="currentColor" {...p}><path d="M8 5v14l11-7z" /></svg>;
const IcoNav     = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M3 11l19-9-9 19-2-8-8-2z" /></svg>;
const IcoCheck2  = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>;

function formatDate(v) {
  if (!v) return null;
  const d = new Date(v);
  return isNaN(d) ? String(v) : d.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "short" });
}

export default function MissionCard({ mission, isExpanded, onToggle, onStepComplete, completedSteps, isActiveNavigation = false, isMissionFinished = false, onStartMission, guidedStepIndex = 0 }) {
  const status = STATUS[mission.status] ?? STATUS.planned;

  const steps = [...(mission.deliveries_order || [])]
    .sort((a, b) => a.order - b.order)
    .map((step) => ({
      ...step,
      completed: completedSteps?.has(`${step.delivery_id}-${step.order}`) || step.completed || false,
    }));

  const doneCount   = steps.filter((s) => s.completed).length;
  const progress    = steps.length > 0 ? Math.round((doneCount / steps.length) * 100) : 0;
  const durationMin = Math.round((mission.route_duration || 0) / 60);
  const dateLabel   = formatDate(mission.date || mission.scheduled_date);
  const region      = mission.region || mission.zone;
  const startTime   = mission.start_time || mission.scheduled_start;

  const canStart = !isActiveNavigation && !isMissionFinished
    && mission.status !== "completed" && mission.status !== "cancelled";

  return (
    <article className={`shrink-0 overflow-hidden rounded-2xl border transition-all duration-200 ${
      isExpanded
        ? "border-brand-light/35 bg-surface shadow-lg shadow-brand/8"
        : "border-border/80 bg-surface/70 hover:border-border-strong hover:bg-surface"
    }`}>

      {/* ── Clickable header ── */}
      <button onClick={onToggle} className="w-full text-left">
        <div className="flex">
          {/* Left status stripe */}
          <div className={`w-[3px] shrink-0 rounded-l-2xl ${status.stripe}`} />

          <div className="min-w-0 flex-1 px-4 py-4">
            {/* Row 1 — ID + badge + date */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[13px] font-bold tracking-tight">
                #{mission._id?.slice(-6) ?? "———"}
              </span>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.badge}`}>
                {status.label}
              </span>
              {dateLabel && (
                <span className="ml-auto font-mono text-[10px] text-tertiary">{dateLabel}</span>
              )}
            </div>

            {/* Row 2 — region + start time */}
            {(region || startTime) && (
              <div className="mt-1.5 flex flex-wrap items-center gap-3 text-[11px] text-tertiary">
                {region    && <span className="flex items-center gap-1"><IcoPin   className="h-3 w-3" />{region}</span>}
                {startTime && <span className="flex items-center gap-1"><IcoClock className="h-3 w-3" />Départ {startTime}</span>}
              </div>
            )}

            {/* Row 3 — stat chips */}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px]">
              <span className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-base/80 px-2 py-1">
                <IcoPackage className="h-3.5 w-3.5 text-brand-light" />
                <span className="font-medium text-secondary">{mission.delivery_ids?.length || steps.length || 0} livraisons</span>
              </span>
              <span className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-base/80 px-2 py-1">
                <IcoRoute className="h-3.5 w-3.5 text-cyan" />
                <span className="font-medium text-secondary">{mission.route_distance ?? 0} km</span>
              </span>
              <span className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-base/80 px-2 py-1">
                <IcoClock className="h-3.5 w-3.5 text-[var(--violet)]" />
                <span className="font-medium text-secondary">{durationMin} min</span>
              </span>
            </div>

            {/* Row 4 — progress bar + chevron */}
            <div className="mt-3 flex items-center gap-2.5">
              {steps.length > 0 ? (
                <>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-hover">
                    <div
                      className="h-full rounded-full bg-brand-light transition-[width] duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <span className="shrink-0 font-mono text-[10px] text-tertiary">{doneCount}/{steps.length}</span>
                </>
              ) : (
                <div className="flex-1" />
              )}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
                className={`h-4 w-4 shrink-0 text-tertiary transition-transform duration-300 ${isExpanded ? "rotate-180" : ""}`}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
      </button>

      {/* ── Action row: start / navigation status ── */}
      {(canStart || isActiveNavigation || isMissionFinished) && (
        <div className="border-t border-border/40 px-4 py-2.5">
          {canStart && (
            <button
              onClick={onStartMission}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-2 text-xs font-semibold text-white transition-all hover:brightness-110 active:scale-[0.98]"
            >
              <IcoPlay className="h-3.5 w-3.5" />
              Commencer la mission
            </button>
          )}
          {isActiveNavigation && !isMissionFinished && (
            <div className="flex items-center gap-2 rounded-xl border border-cyan/20 bg-cyan/10 px-3 py-2 text-xs font-medium text-cyan">
              <IcoNav className="h-3.5 w-3.5 shrink-0" />
              Navigation active · étape {guidedStepIndex + 1}
            </div>
          )}
          {isMissionFinished && (
            <div className="flex items-center gap-2 rounded-xl border border-brand/25 bg-brand/10 px-3 py-2 text-xs font-medium text-brand-light">
              <IcoCheck2 className="h-3.5 w-3.5 shrink-0" />
              Mission terminée — toutes les étapes sont complètes
            </div>
          )}
        </div>
      )}

      {/* ── Expandable detail ── */}
      <div className={`grid transition-all duration-300 ease-in-out ${isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
        <div className="overflow-hidden">
          <div className="space-y-4 border-t border-border/70 bg-base/50 px-4 py-4">
            {mission.vehicle_id && (
              <div className="flex items-center gap-2 text-xs text-tertiary">
                <IcoTruck className="h-3.5 w-3.5 shrink-0" />
                Véhicule
                <span className="font-mono font-medium text-secondary">…{String(mission.vehicle_id).slice(-6)}</span>
              </div>
            )}
            <div>
              <p className="mb-2.5 text-[10px] uppercase tracking-[0.18em] text-tertiary">
                Itinéraire — {doneCount}/{steps.length} terminées
              </p>
              <MissionTimeline
                steps={steps}
                onStepComplete={onStepComplete}
                completedSteps={completedSteps}
                missionId={mission._id}
              />
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}