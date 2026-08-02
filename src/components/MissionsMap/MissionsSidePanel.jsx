import { getDriverDisplayName } from "../../utils/driver";

const STATUS_STYLES = {
  planned: "bg-blue-50 text-blue-700 border-blue-200",
  in_progress: "bg-amber-50 text-amber-700 border-amber-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  cancelled: "bg-red-50 text-red-700 border-red-200",
};

function formatDuration(seconds) {
  if (seconds == null) return "-";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${hours} h ${String(rest).padStart(2, "0")}`;
}

export default function MissionsSidePanel({ missions, selectedId, onSelect }) {
  return (
    <aside className="w-full lg:w-96 shrink-0  border-r border-gray-200 flex flex-col h-full">
      <div className="px-5 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Missions du jour</h2>
        <p className="text-sm text-gray-500">{missions.length} mission(s)</p>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
        {missions.map((mission) => {
          const isSelected = mission._id === selectedId;
          const statusStyle =
            STATUS_STYLES[mission.status] ?? "bg-gray-50 text-gray-700 border-gray-200";

          return (
            <button
              key={mission._id}
              type="button"
              onClick={() => onSelect(mission._id)}
              className={`w-full text-left px-5 py-4 transition-colors hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500 ${
                isSelected ? "bg-indigo-50/70" : ""
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: mission.color }}
                />
                <span className="font-medium text-gray-900 truncate">
                  {getDriverDisplayName(mission.driver)}
                </span>
              </div>

              <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-gray-600">
                <div className="flex justify-between col-span-2">
                  <dt>Véhicule</dt>
                  <dd className="font-medium text-gray-800">{mission.vehicle_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Région</dt>
                  <dd className="font-medium text-gray-800">{mission.region_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Livraisons</dt>
                  <dd className="font-medium text-gray-800">
                    {mission.delivery_ids?.length ?? 0}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Distance</dt>
                  <dd className="font-medium text-gray-800">{mission.route_distance} km</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Durée</dt>
                  <dd className="font-medium text-gray-800">
                    {formatDuration(mission.route_duration)}
                  </dd>
                </div>
              </dl>

              <span
                className={`inline-block mt-2 px-2 py-0.5 rounded-full text-[11px] font-medium border ${statusStyle}`}
              >
                {mission.status}
              </span>
            </button>
          );
        })}

        {missions.length === 0 && (
          <p className="px-5 py-8 text-sm text-gray-400 text-center">
            Aucune mission pour aujourd'hui.
          </p>
        )}
      </div>
    </aside>
  );
}
