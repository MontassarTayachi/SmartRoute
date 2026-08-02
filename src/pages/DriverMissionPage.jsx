// DriverMissionPage.jsx — Mission Control layout
import { useState, useMemo } from "react";
import { useDriverMissions } from "../hooks/useDriverMissions.js";
import MissionCard from "../components/MissionsMap/MissionCard.jsx";
import DriverMap from "../components/MissionsMap/DriverMap.jsx";

// ─── Icons ───────────────────────────────────────────────────────────────────
const IcoRefresh  = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0115-5.3M20 15a9 9 0 01-15 5.3" /></svg>;
const IcoPackage  = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M3.5 8l8.5-4.5L20.5 8v8L12 20.5 3.5 16V8z" /><path strokeLinecap="round" strokeLinejoin="round" d="M3.5 8L12 12.5 20.5 8M12 12.5V20.5" /></svg>;
const IcoRoute    = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><circle cx="6" cy="6" r="2" /><circle cx="18" cy="18" r="2" /><path strokeLinecap="round" d="M6 8v3a4 4 0 004 4h4a4 4 0 004 4" strokeDasharray="2 3" /></svg>;
const IcoClock    = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><circle cx="12" cy="12" r="8.5" /><path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5V12l3 2" /></svg>;
const IcoTarget   = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" fill="currentColor" /></svg>;
const IcoList     = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01m-.01 4h.01" /></svg>;
const IcoMap      = (p) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...p}><path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>;

// ─── Page Header ─────────────────────────────────────────────────────────────
function PageHeader({ user, onRefresh, isRefreshing }) {
  const today = new Date().toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long",
  });
  const initials = (user?.name || "?")
    .split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <header className="relative shrink-0 border-b border-border/70 bg-surface/90 px-5 py-4 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-[11px] uppercase tracking-[0.22em] text-tertiary capitalize">{today}</p>
          <h1 className="mt-0.5 font-display text-lg font-bold tracking-tight">Mission Control</h1>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            onClick={onRefresh}
            title="Actualiser"
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-border/80 bg-base/60 text-tertiary transition-all hover:bg-surface-hover hover:text-secondary"
          >
            <IcoRefresh className={`h-4 w-4 transition-transform duration-500 ${isRefreshing ? "animate-spin" : ""}`} />
          </button>
          {user && (
            <div className="flex items-center gap-2.5 rounded-xl border border-border/70 bg-base/60 px-3 py-1.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-full border border-brand/30 bg-brand/15 text-[10px] font-bold text-brand-light">
                {initials}
              </div>
              <div className="hidden leading-tight sm:block">
                <p className="text-xs font-semibold">{user.name}</p>
                <p className="font-mono text-[10px] text-tertiary">Livreur actif</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

// ─── KPI Strip ────────────────────────────────────────────────────────────────
function KpiStrip({ totals, missionCount, isLoading }) {
  const kpis = [
    { label: "Missions",   value: missionCount,                          icon: <IcoTarget  className="h-4 w-4" />, accent: "text-brand-light bg-brand/10"  },
    { label: "Livraisons", value: totals.deliveries,                      icon: <IcoPackage className="h-4 w-4" />, accent: "text-cyan bg-cyan/10"          },
    { label: "Distance",   value: `${totals.distance.toFixed(1)} km`,     icon: <IcoRoute   className="h-4 w-4" />, accent: "text-[var(--violet)] bg-[var(--violet)]/10" },
    { label: "Durée est.", value: `${Math.round(totals.duration / 60)} min`, icon: <IcoClock className="h-4 w-4" />, accent: "text-brand-light bg-brand/10"  },
  ];
  return (
    <div className="grid shrink-0 grid-cols-4 gap-2 border-b border-border/60 bg-base/80 px-4 py-3">
      {kpis.map(({ label, value, icon, accent }) => (
        <div
          key={label}
          className={`flex flex-col gap-2 rounded-xl border border-border/60 bg-surface/70 px-3 py-2.5 ${
            isLoading ? "opacity-50" : ""
          }`}
        >
          <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${accent}`}>
            {icon}
          </span>
          <div>
            <p className="font-mono text-sm font-bold">{isLoading ? "—" : value}</p>
            <p className="text-[10px] uppercase tracking-wider text-tertiary">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Mobile Bottom Tab Bar ────────────────────────────────────────────────────
function BottomTabBar({ activeTab, onTabChange }) {
  const tabs = [
    { id: "missions", label: "Missions", Icon: IcoList },
    { id: "map",      label: "Carte",    Icon: IcoMap  },
  ];
  return (
    <nav className="lg:hidden shrink-0 border-t border-border/80 bg-surface/95 backdrop-blur-xl">
      <div className="flex">
        {tabs.map(({ id, label, Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => onTabChange(id)}
              className={`flex flex-1 flex-col items-center gap-1 py-3 transition-colors ${
                active ? "text-brand-light" : "text-tertiary"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[11px] font-medium">{label}</span>
              {active && <span className="h-0.5 w-8 rounded-full bg-brand-light" />}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

// ─── Missions Panel ───────────────────────────────────────────────────────────
function MissionsPanel({ missions, isLoading, error, expandedId, onToggle, onStepComplete, completedSteps, activeMissionId, onStartMission, missionFinished, guidedStepIndex }) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-3 overflow-y-auto p-3 thin-scroll">
      {error && (
        <div className="shrink-0 rounded-xl border border-danger/25 bg-danger/10 px-4 py-3 text-sm text-danger-text">
          {error}
        </div>
      )}

      {isLoading && Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-28 shrink-0 animate-pulse rounded-2xl border border-border/60 bg-base/60" />
      ))}

      {!isLoading && !error && missions.length === 0 && (
        <div className="shrink-0 flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border px-4 py-14 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-hover text-tertiary">
            <IcoList className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-semibold text-secondary">Aucune mission planifiée</p>
            <p className="mt-1 text-xs text-tertiary">Votre plan de livraison apparaîtra ici.</p>
          </div>
        </div>
      )}

      {missions.map((mission) => (
        <MissionCard
          key={mission._id}
          mission={mission}
          isExpanded={expandedId === mission._id}
          onToggle={() => onToggle(mission._id)}
          onStepComplete={onStepComplete}
          completedSteps={completedSteps}
          isActiveNavigation={activeMissionId === mission._id}
          isMissionFinished={missionFinished && activeMissionId === mission._id}
          onStartMission={() => onStartMission(mission)}
          guidedStepIndex={activeMissionId === mission._id ? guidedStepIndex : 0}
        />
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function DriverMissionPage() {
  const { user, missions, isLoading, error, refresh } = useDriverMissions();
  const [expandedId, setExpandedId]         = useState(null);
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [activeTab, setActiveTab]           = useState("missions");
  const [isRefreshing, setIsRefreshing]     = useState(false);
  const [activeMissionId, setActiveMissionId]   = useState(null);
  const [guidedStepIndex, setGuidedStepIndex]   = useState(0);
  const [missionFinished, setMissionFinished]   = useState(false);

  const activeMission = useMemo(
    () => missions.find((m) => m._id === activeMissionId) ?? null,
    [missions, activeMissionId]
  );

  const handleStartMission = (mission) => {
    const sorted = [...(mission.deliveries_order || [])].sort((a, b) => a.order - b.order);
    const firstIdx = sorted.findIndex(
      (s) => !completedSteps.has(`${s.delivery_id}-${s.order}`) && !s.completed
    );
    setActiveMissionId(mission._id);
    setMissionFinished(firstIdx === -1);
    setGuidedStepIndex(firstIdx === -1 ? 0 : firstIdx);
    setExpandedId(mission._id);
    setActiveTab("map");
  };

  const handleStepComplete = (step, missionId) => {
    const newCompleted = new Set([...completedSteps, `${step.delivery_id}-${step.order}`]);
    setCompletedSteps(newCompleted);

    if (missionId !== activeMissionId) return;
    const mission = missions.find((m) => m._id === missionId);
    if (!mission) return;

    const sorted = [...(mission.deliveries_order || [])].sort((a, b) => a.order - b.order);
    const nextIdx = sorted.findIndex((s) => !newCompleted.has(`${s.delivery_id}-${s.order}`));
    if (nextIdx === -1) {
      setMissionFinished(true);
    } else {
      setGuidedStepIndex(nextIdx);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refresh();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  const totals = useMemo(
    () => missions.reduce(
      (acc, m) => ({
        distance:   acc.distance   + (m.route_distance || 0),
        duration:   acc.duration   + (m.route_duration || 0),
        deliveries: acc.deliveries + (m.delivery_ids?.length || 0),
      }),
      { distance: 0, duration: 0, deliveries: 0 }
    ),
    [missions]
  );

  return (
    <div className="page-panel flex h-full w-full flex-col overflow-hidden">
      <PageHeader user={user} onRefresh={handleRefresh} isRefreshing={isRefreshing} />
      <KpiStrip totals={totals} missionCount={missions.length} isLoading={isLoading} />

      {/* Main split: missions panel left + map right */}
      <div className="relative flex-1 min-h-0 overflow-hidden lg:grid lg:grid-cols-[380px_1fr]">
        <div className={`${
          activeTab === "missions" ? "flex" : "hidden"
        } lg:flex flex-col h-full min-h-0 border-r border-border/70 bg-base/80 overflow-hidden`}>
          <MissionsPanel
            missions={missions}
            isLoading={isLoading}
            error={error}
            expandedId={expandedId}
            onToggle={(id) => setExpandedId((prev) => (prev === id ? null : id))}
            onStepComplete={handleStepComplete}
            completedSteps={completedSteps}
            activeMissionId={activeMissionId}
            onStartMission={handleStartMission}
            missionFinished={missionFinished}
            guidedStepIndex={guidedStepIndex}
          />
        </div>

        <div className={`${
          activeTab === "map" ? "block" : "hidden"
        } lg:block relative h-full min-h-0 bg-base`}>
          <DriverMap
            missions={missions}
            user={user}
            activeMission={activeMission}
            guidedStepIndex={guidedStepIndex}
            missionFinished={missionFinished}
          />
        </div>
      </div>

      <BottomTabBar activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}