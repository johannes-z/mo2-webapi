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

  if (err) {
    return (
      <pre className="code-block code-block-fallback">
        <code>{code}</code>
      </pre>
    );
  }
  if (!html) return <pre className="code-block">Loading…</pre>;
  return <div className="code-block shiki" dangerouslySetInnerHTML={{ __html: html }} />;
}
