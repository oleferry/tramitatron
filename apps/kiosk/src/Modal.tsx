import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

// Elementos que pueden recibir el foco por tabulación, para atrapar el
// tabulador dentro del diálogo (un modal de verdad no deja escapar el foco).
const FOCUSABLE =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

/**
 * Diálogo modal accesible (WCAG 2.4.3 y patrón ARIA de alertdialog).
 *
 * Al abrirse lleva el foco al propio diálogo —así el lector de pantalla anuncia
 * título y cuerpo— sin dejar armado ningún botón (importa en el de "terminar y
 * borrar", que es destructivo). Atrapa el tabulador dentro, cierra con Escape
 * por la salida MENOS destructiva (`onEscape`) y, al desmontarse, devuelve el
 * foco a donde estaba antes de abrir.
 */
export function Modal({
  titleId,
  bodyId,
  onEscape,
  children,
}: {
  titleId: string;
  bodyId?: string;
  onEscape?: () => void;
  children: ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  // El manejador de Escape se lee por ref para que el efecto se monte una sola
  // vez: si dependiera de `onEscape` (que cambia de identidad en cada render),
  // el foco saltaría al diálogo en cada repintado.
  const onEscapeRef = useRef(onEscape);
  onEscapeRef.current = onEscape;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;

    dialog.focus({ preventScroll: true });

    const items = () =>
      Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (el) => !el.hasAttribute("disabled"),
      );

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (onEscapeRef.current) {
          e.preventDefault();
          onEscapeRef.current();
        }
        return;
      }
      if (e.key !== "Tab") return;
      const focusables = items();
      if (focusables.length === 0) {
        e.preventDefault();
        return;
      }
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;
      // Enrolla el foco en los extremos; y si está en el propio diálogo (estado
      // inicial), Shift+Tab va al último en vez de escapar hacia atrás.
      if (e.shiftKey && (active === first || active === dialog)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    };

    dialog.addEventListener("keydown", onKeyDown);
    return () => {
      dialog.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus?.({ preventScroll: true });
    };
  }, []);

  return (
    <div className="modal-overlay">
      <div
        className="modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={bodyId}
        tabIndex={-1}
        ref={dialogRef}
      >
        {children}
      </div>
    </div>
  );
}
