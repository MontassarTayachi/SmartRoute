// MissionTimeline.jsx
import { useState } from "react";
import { updateMissionStep } from "../../services/missionService";

const PICKUP_COLOR = "#F5A623";

function IconChevron({ open }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      className={`h-3.5 w-3.5 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function IconCheck() {
  return (
    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth={3}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function IconUser(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <circle cx="12" cy="8" r="3.2" />
      <path strokeLinecap="round" d="M5 20c1.2-3.5 4-5.2 7-5.2s5.8 1.7 7 5.2" />
    </svg>
  );
}

function IconPhone(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6.6 10.8a13 13 0 006.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C11.6 21 3 12.4 3 2.9c0-.6.4-1 1-1h3.4c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"
      />
    </svg>
  );
}

function IconWeight(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <circle cx="12" cy="6" r="2.5" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.4 8.5h7.2l2 11.5a1 1 0 01-1 1.2H7.4a1 1 0 01-1-1.2l2-11.5z" />
    </svg>
  );
}

function IconRoute(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <circle cx="6" cy="6" r="2" />
      <circle cx="18" cy="18" r="2" />
      <path strokeLinecap="round" d="M6 8v3a4 4 0 004 4h4a4 4 0 004 4" strokeDasharray="2 3" />
    </svg>
  );
}

function IconClock(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5V12l3 2" />
    </svg>
  );
}

function IconFlag(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 21V4m0 1.5h11l-2.6 3.5L17 12.5H6" />
    </svg>
  );
}

const PRIORITY_STYLES = {
  high: { label: "Urgente", className: "bg-danger/10 text-danger-text" },
  normal: { label: "Normale", className: "bg-surface-hover text-tertiary" },
  low: { label: "Faible", className: "bg-brand-light/10 text-brand-light" },
};

function DetailRow({ icon, label, value }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="flex items-center gap-2 min-w-0">
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-surface-hover text-tertiary">
        {icon}
      </span>
      <div className="min-w-0 leading-tight">
        <p className="text-[9px] uppercase tracking-wider text-tertiary">{label}</p>
        <p className="text-xs font-medium text-secondary truncate">{value}</p>
      </div>
    </div>
  );
}

export default function MissionTimeline({ steps, onStepComplete, completedSteps = new Set(), missionId }) {
  const [openId, setOpenId] = useState(null);
  const [loadingStep, setLoadingStep] = useState(null);

  if (!steps || steps.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-hover text-tertiary">
          <IconRoute className="h-5 w-5" />
        </span>
        <p className="text-xs text-tertiary">Aucune étape pour cette mission.</p>
      </div>
    );
  }

  // Regroupe les étapes par livraison pour retrouver l'adresse "compagnon"
  // (le point de ramassage associé à une livraison, ou inversement).
  const byDelivery = steps.reduce((acc, s) => {
    (acc[s.delivery_id] ||= []).push(s);
    return acc;
  }, {});

  const handleStepComplete = async (step) => {
    if (!missionId) {
      console.error("missionId manquant pour la mise à jour de l'étape");
      return;
    }

    try {
      setLoadingStep(step.order);
      await updateMissionStep(missionId, step.order, true);
      if (onStepComplete) {
        onStepComplete(step, missionId);
      }
    } catch (error) {
      console.error("Erreur lors de la mise à jour de l'étape:", error);
      alert("Erreur lors de la mise à jour de l'étape. Veuillez réessayer.");
    } finally {
      setLoadingStep(null);
    }
  };

  return (
    <ol className="relative">
      {steps.map((step, idx) => {
        const key = `${step.delivery_id}-${step.order}`;
        const isDone = completedSteps.has(key) || step.completed || step.is_done;
        const isLast = idx === steps.length - 1;
        const isPickup = step.step_type === "pickup";
        const isOpen = openId === key;
        const isLoading = loadingStep === step.order;

        const companion = (byDelivery[step.delivery_id] || []).find(
          (s) => s.step_type !== step.step_type
        );

        const priority = PRIORITY_STYLES[step.priority] || null;
        const legDistance = step.distance ?? step.leg_distance;
        const legDuration = step.duration ?? step.leg_duration;
        const customerName = step.customer_name ?? step.client_name;
        const customerPhone = step.customer_phone ?? step.phone;
        const weight = step.weight ?? step.package_weight;

        const accentColor = isPickup ? PICKUP_COLOR : "var(--color-cyan, #2DD4BF)";

        return (
          <li key={key} className="relative flex gap-3 pb-3 last:pb-0">
            {!isLast && (
              <span
                className={`absolute left-[13px] top-7 bottom-0 w-px ${
                  isDone ? "bg-brand-light/50" : "bg-border"
                }`}
              />
            )}

            {/* Puce d'étape */}
            <button
              type="button"
              onClick={() => !isDone && !isLoading && handleStepComplete(step)}
              disabled={isDone || isLoading}
              className={`relative z-10 mt-3 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                isDone ? "bg-brand-light border-brand-light text-base-inverse cursor-default" : "bg-base"
              } ${isLoading ? "opacity-50 cursor-wait" : ""}`}
              style={!isDone ? { borderColor: accentColor, color: accentColor } : undefined}
              title={isDone ? "Étape terminée" : isLoading ? "Mise à jour..." : "Marquer comme terminée"}
            >
              {isLoading ? (
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 animate-spin" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
                </svg>
              ) : isDone ? (
                <IconCheck />
              ) : (
                <span className="font-mono text-[11px] font-semibold">{step.order + 1}</span>
              )}
            </button>

            {/* Carte d'étape */}
            <div
              className={`flex-1 min-w-0 rounded-lg border transition-colors ${
                isOpen ? "border-brand-light/30 bg-surface-hover/60" : "border-border/70 bg-base"
              } ${isDone ? "opacity-60" : ""}`}
            >
              <button
                type="button"
                onClick={() => setOpenId(isOpen ? null : key)}
                className="w-full flex items-center gap-2 px-3 py-2.5 text-left"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="text-[10px] font-mono uppercase tracking-wider font-semibold"
                      style={{ color: accentColor }}
                    >
                      {isPickup ? "Ramassage" : "Livraison"} · #{step.order + 1}
                    </span>
                    {priority && (
                      <span className={`text-[9px] font-mono font-medium px-1.5 py-0.5 rounded ${priority.className}`}>
                        {priority.label}
                      </span>
                    )}
                    {isDone && (
                      <span className="text-[10px] font-mono text-brand-light">Terminée</span>
                    )}
                  </div>
                  <p className={`text-sm truncate mt-0.5 ${isDone ? "line-through" : ""}`}>{step.address}</p>
                  {customerName && (
                    <p className="text-[11px] text-tertiary truncate">{customerName}</p>
                  )}
                </div>
                <IconChevron open={isOpen} />
              </button>

              <div className={`grid transition-all duration-200 ${isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
                <div className="overflow-hidden">
                  <div className="px-3 pb-3 pt-1 border-t border-border/60 grid grid-cols-2 gap-x-3 gap-y-2.5">
                    <DetailRow
                      icon={<span className="h-2 w-2 rounded-full" style={{ background: PICKUP_COLOR }} />}
                      label="Adresse de départ"
                      value={isPickup ? step.address : companion?.address}
                    />
                    <DetailRow
                      icon={<span className="h-2 w-2 rounded-full bg-cyan" />}
                      label="Adresse d'arrivée"
                      value={isPickup ? companion?.address : step.address}
                    />
                    <DetailRow icon={<IconUser className="h-3.5 w-3.5" />} label="Client" value={customerName} />
                    <DetailRow icon={<IconPhone className="h-3.5 w-3.5" />} label="Téléphone" value={customerPhone} />
                    <DetailRow
                      icon={<IconWeight className="h-3.5 w-3.5" />}
                      label="Poids"
                      value={weight != null ? `${weight} kg` : null}
                    />
                    <DetailRow
                      icon={<IconRoute className="h-3.5 w-3.5" />}
                      label="Distance"
                      value={legDistance != null ? `${Number(legDistance).toFixed(1)} km` : null}
                    />
                    <DetailRow
                      icon={<IconClock className="h-3.5 w-3.5" />}
                      label="Temps estimé"
                      value={legDuration != null ? `${Math.round(legDuration / 60)} min` : null}
                    />
                    <DetailRow
                      icon={<IconFlag className="h-3.5 w-3.5" />}
                      label="Statut"
                      value={isDone ? "Terminée" : "En attente"}
                    />
                    <DetailRow
                      icon={
                        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth={1.8}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 21s-7-6.2-7-11a7 7 0 1114 0c0 4.8-7 11-7 11z" />
                          <circle cx="12" cy="10" r="2.4" />
                        </svg>
                      }
                      label="Coordonnées"
                      value={`${step.lat?.toFixed(5)}, ${step.lng?.toFixed(5)}`}
                    />
                  </div>
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}