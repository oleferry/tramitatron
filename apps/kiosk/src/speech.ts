// Lectura en voz alta (PRD §14.2: "lectura en voz alta", control de volumen
// y repetición).
//
// Se usa la síntesis LOCAL del navegador (SpeechSynthesis), no un proveedor
// externo: el texto que se lee incluye contenido de cartas y datos del
// ciudadano, y enviarlo a un servicio de terceros para convertirlo en audio
// sería exactamente lo que el PRD §13.2 prohíbe. Además funciona sin red y
// sin latencia. Ver ADR-005.

import type { Lang } from "./i18n";

const VOICE_LANG: Record<Lang, string> = {
  es: "es-ES",
  // Los navegadores no suelen traer voz valenciana; el catalán es el más
  // cercano y, si tampoco está, se cae a la voz por defecto del sistema.
  "ca-valencia": "ca-ES",
};

export function speechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/** Corta cualquier lectura en curso. */
export function stopSpeaking(): void {
  if (speechSupported()) window.speechSynthesis.cancel();
}

/**
 * Lee un texto en voz alta. Cancela lo anterior para que pulsar dos veces no
 * solape voces (y para que "repetir" sea simplemente volver a pulsar).
 */
export function speak(text: string, lang: Lang): void {
  if (!speechSupported() || !text.trim()) return;
  stopSpeaking();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = VOICE_LANG[lang];
  // Algo más lento que el habla normal: el público objetivo son personas
  // mayores o con baja competencia digital (PRD §14.2, "textos breves").
  utterance.rate = 0.92;
  const preferred = window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang.startsWith(VOICE_LANG[lang].slice(0, 2)));
  if (preferred) utterance.voice = preferred;
  window.speechSynthesis.speak(utterance);
}
