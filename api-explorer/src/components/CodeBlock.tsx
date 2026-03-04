import { useEffect, useState } from "react";
import { codeToHtml } from "shiki";

interface CodeBlockProps {
  code: string;
  lang?: string;
}

export function CodeBlock({ code, lang = "json" }: CodeBlockProps) {
  const [html, setHtml] = useState<string>("");
  const [err, setErr] = useState(false);

  useEffect(() => {
    codeToHtml(code, {
      lang,
      theme: "github-dark",
    })
      .then(setHtml)
      .catch(() => setErr(true));
  }, [code, lang]);

  const blockClass =
    "font-mono text-xs bg-bg border border-border rounded-md px-3 py-2 overflow-x-auto whitespace-pre-wrap break-words m-0";
  if (err) {
    return <pre className={blockClass}><code>{code}</code></pre>;
  }
  if (!html) return <pre className={blockClass}>Loading…</pre>;
  return (
    <div
      className={`${blockClass} [&_pre]:m-0 [&_pre]:bg-transparent!`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
