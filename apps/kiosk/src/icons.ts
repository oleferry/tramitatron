// Icono por trámite (por prefijo del id). Icono + texto siempre (PRD §14.2).

const ICONS: [string, string][] = [
  ["sacyl.health.card", "💳"],
  ["sacyl.health", "🩺"],
  ["jcyl.itv", "🚗"],
  ["mir.dni", "🪪"],
  ["mir.extranjeria", "🌍"],
  ["aeat", "🧾"],
  ["seg-social.tgss", "📋"],
  ["seg-social", "🧓"],
  ["sepe", "💼"],
  ["dgt", "🚦"],
  ["padron", "🏠"],
  ["mjusticia", "⚖️"],
  ["demo.worker", "🩺"],
  ["demo.hacienda", "🧾"],
  ["demo.inss", "🧓"],
  ["demo", "✨"],
];

export function procedureIcon(procedureId: string): string {
  const match = ICONS.find(([prefix]) => procedureId.startsWith(prefix));
  return match ? match[1] : "📄";
}
