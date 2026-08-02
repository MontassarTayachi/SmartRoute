/**
 * Retourne un nom lisible pour un livreur, quelle que soit la forme
 * exacte de l'objet renvoyé par driverService.getDrivers().
 */
export function getDriverDisplayName(driver) {
  if (!driver) return "Livreur inconnu";
  if (driver.name) return driver.name;
  if (driver.full_name) return driver.full_name;
  if (driver.first_name || driver.last_name) {
    return [driver.first_name, driver.last_name].filter(Boolean).join(" ");
  }
  return `Livreur #${driver.id ?? driver._id ?? "?"}`;
}
