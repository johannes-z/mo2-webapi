import { useEffect, useState } from "react";
import { ApiSection } from "./components/ApiSection";
import { BaseUrlInput } from "./components/BaseUrlInput";
import { sections } from "./data/endpoints";

const DEFAULT_BASE = "http://localhost:5000";

export function App() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE);

  useEffect(() => {
    // When served from plugin at same origin, fetch /config to get actual port
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

  return (
    <div className="max-w-200 mx-auto">
      <h1 className="text-xl font-semibold tracking-tight mb-1">MO2 WebAPI</h1>
      <p className="text-sm text-muted mb-6">API overview for Mod Organizer 2.</p>
      <BaseUrlInput value={baseUrl} onChange={setBaseUrl} />
      {sections.map((section) => (
        <ApiSection key={section.title} section={section} baseUrl={baseUrl} />
      ))}
    </div>
  );
}
