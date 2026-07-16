// Icono por trámite (por prefijo del id). Icono + texto siempre (PRD §14.2).

const ICONS: [string, string][] = [
  ["gva.health", "🩺"],
  ["sitval", "🚗"],
  ["demo", "✨"],
];

export function procedureIcon(procedureId: string): string {
  const match = ICONS.find(([prefix]) => procedureId.startsWith(prefix));
  return match ? match[1] : "📄";
}
