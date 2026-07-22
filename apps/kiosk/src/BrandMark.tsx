// Marca de Tramitatrón incrustada como SVG (no como <img src="/icon.svg">).
// Servida bajo /app, una ruta absoluta a /icon.svg daba 404; inline no depende
// de ninguna ruta ni petición, así que carga siempre. Es decorativa: el nombre
// "Tramitatrón" acompaña en texto.
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 400 400"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <rect width="400" height="400" rx="90" fill="#17324D" />
      <path d="M100 102 H300" stroke="#FFFFFF" strokeWidth="44" strokeLinecap="round" />
      <path d="M200 102 V260" stroke="#FFFFFF" strokeWidth="44" strokeLinecap="round" />
      <path
        d="M200 260 C200 315,260 325,300 286"
        fill="none"
        stroke="#F2C14E"
        strokeWidth="32"
        strokeLinecap="round"
      />
      <path
        d="M270 288 L297 315 L345 256"
        fill="none"
        stroke="#F2C14E"
        strokeWidth="28"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
