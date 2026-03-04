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

  return (
    <div className="try-inline">
      <label>
        Path
        <input
          type="text"
          className="try-path"
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
      </label>
      {["POST", "PATCH", "PUT"].includes(method) && (
        <label>
          Body
          <textarea
            className="try-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
          />
        </label>
      )}
      <button type="button" className="try-send" onClick={handleSend}>
        Send
      </button>
      <div
        className={`try-response ${responseOk === true ? "ok" : ""} ${responseOk === false ? "error" : ""}`}
      >
        {response === "(click Send)" || response === "Loading…" ? (
          <pre className="try-response-plain">{response}</pre>
        ) : (
          <CodeBlock code={response} lang={responseLang(response)} />
        )}
      </div>
    </div>
  );
}
