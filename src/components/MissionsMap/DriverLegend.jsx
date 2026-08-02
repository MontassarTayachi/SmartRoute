import { getDriverDisplayName } from "../../utils/driver";

export default function DriverLegend({ drivers, driverColorMap }) {
  if (!drivers.length) return null;

  return (
    <div className="absolute bottom-4 left-4 z-[1000] bg-white/95 backdrop-blur rounded-xl shadow-lg border border-gray-200 p-3 max-h-64 overflow-y-auto w-48">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Livreurs
      </p>
      <ul className="space-y-1.5">
        {drivers.map((driver) => {
          const id = driver.id ?? driver._id;
          return (
            <li key={id} className="flex items-center gap-2 text-sm text-gray-700">
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: driverColorMap[id] }}
              />
              <span className="truncate">{getDriverDisplayName(driver)}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
