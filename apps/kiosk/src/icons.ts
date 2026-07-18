// Icono por trámite (por prefijo del id). Icono + texto siempre (PRD §14.2).

const ICONS: [string, string][] = [
  ["gva.health.sip", "💳"],
  ["gva.health", "🩺"],
  ["sitval", "🚗"],
  ["mir.dni", "🪪"],
  ["mir.extranjeria", "🌍"],
  ["aeat", "🧾"],
  ["seg-social.tgss", "📋"],
  ["seg-social", "🧓"],
  ["sepe", "💼"],
  ["dgt", "🚦"],
  ["castello.padron", "🏠"],
  ["mjusticia", "⚖️"],
  ["demo", "✨"],
];

export function procedureIcon(procedureId: string): string {
  const match = ICONS.find(([prefix]) => procedureId.startsWith(prefix));
  return match ? match[1] : "📄";
}
