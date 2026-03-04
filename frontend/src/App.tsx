import { useEffect, useState } from "react";

export function App() {
  const [health, setHealth] = useState<string | null>(null);

  useEffect(() => {
    const base = typeof window !== "undefined" ? window.location.origin : "";
    if (base) {
      fetch(`${base}/config`)
        .then((r) => r.json())
        .then((cfg: { httpPort?: number }) => {
          const url =
            cfg?.httpPort != null
              ? `${window.location.protocol}//${window.location.hostname}:${cfg.httpPort}`
              : base;
          return fetch(`${url}/health`).then((r) => r.json());
        })
        .then((data) => setHealth(JSON.stringify(data, null, 2)))
        .catch(() => setHealth("(API not reachable)"));
    }
  }, []);

  return (
    <div
      style={{
        fontFamily: "system-ui",
        maxWidth: 800,
        margin: "50px auto",
        padding: 20,
      }}
    >
      <h1>MO2 WebAPI – Frontend</h1>
      <p>Stub frontend for Mod Organizer 2 Web API.</p>
      <p>
        <a href="/api-docs/">API Explorer</a>
      </p>
      <h2>Health</h2>
      <pre style={{ background: "#f4f4f4", padding: 16, borderRadius: 8 }}>
        {health ?? "Loading…"}
      </pre>
    </div>
  );
}
