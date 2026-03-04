import { useEffect, useState } from "react";
import { ApiSection } from "./components/ApiSection";
import { BaseUrlInput } from "./components/BaseUrlInput";
import { sections as staticSections } from "./data/endpoints";
import { openApiToSections } from "./data/openapi";
import type { OpenApiSpec } from "./data/openapi";
import type { SectionDef } from "./data/endpoints";

const DEFAULT_BASE = "http://localhost:5000";

export function App() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE);
  const [sections, setSections] = useState<SectionDef[]>(staticSections);
  const [specError, setSpecError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const origin = window.location.origin;
    fetch(`${origin}/config`)
      .then((r) => r.json())
      .then((cfg: { httpPort?: number }) => {
        if (cfg?.httpPort != null) {
          const u = new URL(origin);
          u.port = String(cfg.httpPort);
          setBaseUrl(u.origin);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setSpecError(null);
    const url = `${baseUrl.replace(/\/$/, "")}/openapi.json`;
    fetch(url)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then((spec: OpenApiSpec) => {
        const fromSpec = openApiToSections(spec);
        setSections(fromSpec.length ? fromSpec : staticSections);
      })
      .catch(() => {
        setSections(staticSections);
        setSpecError("OpenAPI spec unavailable, showing static docs.");
      });
  }, [baseUrl]);

  return (
    <div className="max-w-content mx-auto">
      <h1 className="text-xl font-semibold tracking-tight mb-1">MO2 WebAPI</h1>
      <p className="text-sm text-muted mb-6">API overview for Mod Organizer 2.</p>
      <BaseUrlInput value={baseUrl} onChange={setBaseUrl} />
      {specError && (
        <p className="text-xs text-muted mb-4" role="status">
          {specError}
        </p>
      )}
      {sections.map((section) => (
        <ApiSection key={section.title} section={section} baseUrl={baseUrl} />
      ))}
    </div>
  );
}
