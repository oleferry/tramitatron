import type { Lang } from "../i18n";
import { t } from "../i18n";

// La pantalla de idioma muestra ambos títulos: aún no sabemos qué habla el usuario.
export function LanguageScreen({ onChoose }: { onChoose: (lang: Lang) => void }) {
  return (
    <div className="screen">
      <div className="language-hero" aria-hidden="true">
        👋
      </div>
      <h2>
        {t("es").chooseLanguage} / {t("ca-valencia").chooseLanguage}
      </h2>
      <div className="language-buttons">
        <button className="btn-primary btn-xl" onClick={() => onChoose("es")} lang="es">
          {t("es").languageEs}
        </button>
        <button
          className="btn-primary btn-xl"
          onClick={() => onChoose("ca-valencia")}
          lang="ca-valencia"
        >
          {t("es").languageVa}
        </button>
      </div>
    </div>
  );
}
