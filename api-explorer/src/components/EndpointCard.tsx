import { useState } from "react";
import type { EndpointDef, HttpMethod } from "../data/endpoints";
import { CodeBlock } from "./CodeBlock";
import { TryItInline } from "./TryItInline";

const METHOD_CLASS: Record<Lowercase<HttpMethod>, string> = {
  get: "bg-get/20 text-get",
  post: "bg-post/20 text-post",
  patch: "bg-patch/20 text-patch",
  put: "bg-put/20 text-put",
  delete: "bg-delete/20 text-delete",
};

interface EndpointCardProps {
  endpoint: EndpointDef;
  baseUrl: string;
}

export function EndpointCard({ endpoint, baseUrl }: EndpointCardProps) {
  const [showTry, setShowTry] = useState(false);
  const methodKey = endpoint.method.toLowerCase() as Lowercase<HttpMethod>;

  return (
    <details className="endpoint bg-surface border border-border rounded-lg mb-0.5 overflow-hidden">
      <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer font-medium">
        <span
          className={`font-mono text-xs font-medium px-1.5 py-0.5 rounded min-w-[3.2rem] text-center ${METHOD_CLASS[methodKey]}`}
        >
          {endpoint.method}
        </span>
        <span className="font-mono text-sm text-text">{endpoint.path}</span>
      </summary>
      <div className="p-4 border-t border-border">
        <div className="endpoint-docs [&>div]:mt-3 [&>div:first-child]:mt-0">
          {endpoint.docs.map((d) =>
            typeof d === "string" ? (
              <p key={d.slice(0, 80)} className="text-sm text-muted mt-2 mb-1 first:mt-0">
                {d}
              </p>
            ) : (
              <div key={`${d.title}-${d.content.slice(0, 40)}`}>
                <h4 className="text-xs uppercase tracking-wide text-muted mt-2 mb-1 first:mt-0">
                  {d.title}
                </h4>
                <CodeBlock code={d.content} />
              </div>
            ),
          )}
        </div>
        <button
          type="button"
          className="mt-3 px-3 py-1.5 bg-accent text-white rounded-md text-sm font-semibold cursor-pointer hover:bg-accent-hover"
          onClick={() => setShowTry((s) => !s)}
        >
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
