import { useState } from "react";
import type { HttpMethod } from "../data/endpoints";
import { CodeBlock } from "./CodeBlock";

interface TryItInlineProps {
  baseUrl: string;
  method: HttpMethod;
  defaultPath: string;
  defaultBody: string;
}

function responseLang(text: string): "json" | "text" {
  if (!text || text === "(click Send)" || text === "Loading…") return "text";
  try {
    JSON.parse(text);
    return "json";
  } catch {
    return "text";
  }
}

export function TryItInline({ baseUrl, method, defaultPath, defaultBody }: TryItInlineProps) {
  const [path, setPath] = useState(defaultPath);
  const [body, setBody] = useState(defaultBody);
  const [response, setResponse] = useState<string>("(click Send)");
  const [responseOk, setResponseOk] = useState<boolean | null>(null);

  async function handleSend() {
    const base = (baseUrl || "").replace(/\/$/, "");
    const pathNorm = (path || "").replace(/^\//, "/");
    const url = base + pathNorm;
    setResponse("Loading…");
    setResponseOk(null);
    try {
      const opts: RequestInit = { method };
      if (body.trim() && ["POST", "PATCH", "PUT"].includes(method)) {
        opts.headers = { "Content-Type": "application/json" };
        opts.body = body.trim();
      }
      const r = await fetch(url, opts);
      const text = await r.text();
      let data: unknown;
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
      setResponse(typeof data === "string" ? data : JSON.stringify(data, null, 2));
      setResponseOk(r.ok);
    } catch (err) {
      setResponse(String(err));
      setResponseOk(false);
    }
  }

  const responseBorder =
    responseOk === true ? "border-get" : responseOk === false ? "border-delete" : "border-border";

  return (
    <div className="mt-4 pt-4 border-t border-border">
      <label className="block mt-2 text-sm text-muted first:mt-0">
        Path
        <input
          type="text"
          className="w-full mt-0.5 px-2.5 py-1.5 bg-bg border border-border rounded-md text-text font-mono text-sm block"
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
      </label>
      {["POST", "PATCH", "PUT"].includes(method) && (
        <label className="block mt-2 text-sm text-muted">
          Body
          <textarea
            className="w-full mt-0.5 px-2.5 py-1.5 bg-bg border border-border rounded-md text-text font-mono text-sm min-h-20 resize-y block"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
          />
        </label>
      )}
      <button
        type="button"
        className="mt-3 px-4 py-1.5 bg-accent text-white rounded-md text-sm font-semibold cursor-pointer hover:bg-accent-hover"
        onClick={handleSend}
      >
        Send
      </button>
      <div
        className={`mt-3 min-h-12 text-sm border rounded-md p-3 whitespace-pre-wrap border-border [&>div]:m-0 [&>div]:border-0 [&>pre]:m-0 [&>pre]:border-0 ${responseBorder}`}
      >
        {response === "(click Send)" || response === "Loading…" ? (
          <pre className="text-sm text-muted m-0">{response}</pre>
        ) : (
          <CodeBlock code={response} lang={responseLang(response)} />
        )}
      </div>
    </div>
  );
}
