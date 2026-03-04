import { useState } from "react";
import type { EndpointDef } from "../data/endpoints";
import { CodeBlock } from "./CodeBlock";
import { TryItInline } from "./TryItInline";

interface EndpointCardProps {
  endpoint: EndpointDef;
  baseUrl: string;
}

export function EndpointCard({ endpoint, baseUrl }: EndpointCardProps) {
  const [showTry, setShowTry] = useState(false);

  return (
    <details className="endpoint">
      <summary>
        <span className={`method ${endpoint.method.toLowerCase()}`}>{endpoint.method}</span>
        <span className="path">{endpoint.path}</span>
      </summary>
      <div className="endpoint-body">
        <div className="endpoint-docs">
          {endpoint.docs.map((d) =>
            typeof d === "string" ? (
              <p key={d.slice(0, 80)}>{d}</p>
            ) : (
              <div key={`${d.title}-${d.content.slice(0, 40)}`}>
                <h4>{d.title}</h4>
                <CodeBlock code={d.content} />
              </div>
            ),
          )}
        </div>
        <button type="button" className="try-open" onClick={() => setShowTry((s) => !s)}>
          Try it
        </button>
        {showTry && (
          <TryItInline
            baseUrl={baseUrl}
            method={endpoint.method}
            defaultPath={endpoint.path}
            defaultBody={endpoint.body ?? ""}
          />
        )}
      </div>
    </details>
  );
}
