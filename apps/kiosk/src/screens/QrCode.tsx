import qrcode from "qrcode-generator";

/**
 * Código QR renderizado como SVG inline. Se genera EN EL NAVEGADOR, sin ninguna
 * petición externa (privacidad y CSP): la librería es pura y se empaqueta en el
 * build. Colores de marca (azul marino sobre blanco) con contraste de sobra
 * para que cualquier cámara lo lea. Incluye la zona de silencio (4 módulos).
 *
 * OJO: la URL que se codifica no debe llevar datos personales; en el handoff
 * del worker solo son selecciones del trámite (servicio, oficina, fecha).
 */
export function QrCode({
  value,
  label,
  size = 220,
}: {
  value: string;
  label: string;
  size?: number;
}) {
  const qr = qrcode(0, "M");
  qr.addData(value);
  qr.make();
  const count = qr.getModuleCount();
  const margin = 4;
  const dim = count + margin * 2;

  let path = "";
  for (let row = 0; row < count; row++) {
    for (let col = 0; col < count; col++) {
      if (qr.isDark(row, col)) {
        path += `M${col + margin} ${row + margin}h1v1h-1z`;
      }
    }
  }

  return (
    <svg
      className="qr"
      role="img"
      aria-label={label}
      width={size}
      height={size}
      viewBox={`0 0 ${dim} ${dim}`}
      shapeRendering="crispEdges"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width={dim} height={dim} fill="#ffffff" />
      <path d={path} fill="#17324d" />
    </svg>
  );
}
