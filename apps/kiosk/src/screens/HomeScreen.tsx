import { useEffect, useState } from "react";

import type { CatalogItem } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";

export function HomeScreen({
  lang,
  onOpenProcedure,
}: {
  lang: Lang;
  onOpenProcedure: (id: string) => void;
}) {
  const strings = t(lang);
  const [catalog, setCatalog] = useState<CatalogItem[] | null>(null);
  const [query, setQuery] = useState("");
  const [clarification, setClarification] = useState<string | null>(null);
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api
      .getCatalog()
      .then(setCatalog)
      .catch(() => setFailed(true));
  }, []);

  const search = async () => {
    const text = query.trim();
    if (!text) return;
    setClarification(null);
    setHighlighted(null);
    try {
      const result = await api.classifyIntent(text, lang);
      if (result.next_action === "SHOW_PROCEDURE" && result.procedure_id) {
        setHighlighted(result.procedure_id);
        onOpenProcedure(result.procedure_id);
      } else {
        setClarification(result.clarification ?? strings.apiError);
      }
    } catch {
      setFailed(true);
    }
  };

  return (
    <div className="screen">
      <h2>{strings.homeTitle}</h2>
      <p className="subtitle">{strings.homeSubtitle}</p>

      <div className="search-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void search()}
          placeholder={strings.searchPlaceholder}
          aria-label={strings.searchPlaceholder}
        />
        <button className="btn-primary" onClick={() => void search()}>
          {strings.searchButton}
        </button>
      </div>

      {clarification && <div className="clarification">{clarification}</div>}
      {failed && <div className="banner banner-info">{strings.apiError}</div>}
      {!catalog && !failed && <p className="subtitle">{strings.loading}</p>}

      {catalog && (
        <>
          <p className="subtitle">{strings.searchHint}</p>
          <div className="cards">
            {catalog.map((item) => (
              <button
                key={item.id}
                className={`card${highlighted === item.id ? " highlighted" : ""}`}
                onClick={() => onOpenProcedure(item.id)}
              >
                <span
                  className={`badge ${
                    item.status === "available" ? "badge-available" : "badge-coming"
                  }`}
                >
                  {item.status === "available"
                    ? strings.statusAvailable
                    : strings.statusComingSoon}
                </span>
                <h3>{item.name[lang]}</h3>
                {item.description && <p>{item.description[lang]}</p>}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
