/** Minimal OpenAPI 3.0 types for spec consumed from GET /openapi.json */

export interface OpenApiOperation {
  summary?: string;
  description?: string;
  tags?: string[];
  requestBody?: {
    content?: {
      "application/json"?: { schema?: object; example?: unknown };
    };
  };
  responses?: Record<string, { description?: string }>;
}

export interface OpenApiPathItem {
  get?: OpenApiOperation;
  post?: OpenApiOperation;
  patch?: OpenApiOperation;
  put?: OpenApiOperation;
  delete?: OpenApiOperation;
}

export interface OpenApiSpec {
  openapi?: string;
  info?: { title?: string; version?: string };
  tags?: Array<{ name: string }>;
  paths?: Record<string, OpenApiPathItem>;
}

export type HttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

const METHODS: HttpMethod[] = ["GET", "POST", "PATCH", "PUT", "DELETE"];

function getRequestBodyExample(op: OpenApiOperation): string {
  const content = op.requestBody?.content?.["application/json"];
  if (!content?.example) return "";
  return JSON.stringify(content.example, null, 2);
}

import type { DocBlock, EndpointDef, SectionDef } from "./endpoints";

/** Convert OpenAPI 3.0 spec to SectionDef[] for the explorer. */
export function openApiToSections(spec: OpenApiSpec): SectionDef[] {
  const paths = spec.paths ?? {};
  const tagOrder = (spec.tags ?? []).map((t) => t.name);
  const sectionMap = new Map<string, EndpointDef[]>();

  for (const [path, pathItem] of Object.entries(paths)) {
    if (!pathItem) continue;
    for (const method of METHODS) {
      const op = pathItem[method.toLowerCase() as keyof OpenApiPathItem] as OpenApiOperation | undefined;
      if (!op) continue;
      const tag = op.tags?.[0] ?? "API";
      const docs: (string | DocBlock)[] = [];
      if (op.summary) docs.push(op.summary);
      if (op.description) docs.push(op.description);
      const bodyExample = getRequestBodyExample(op);
      if (bodyExample) {
        docs.push({ title: "Request", content: bodyExample });
      }
      const firstResponse = op.responses?.["200"] ?? op.responses?.["201"] ?? Object.values(op.responses ?? {})[0];
      if (firstResponse?.description) {
        docs.push({ title: "Response", content: firstResponse.description });
      }
      const endpoint: EndpointDef = {
        method,
        path,
        body: bodyExample || undefined,
        docs: docs.length ? docs : ["No description."],
      };
      const list = sectionMap.get(tag) ?? [];
      list.push(endpoint);
      sectionMap.set(tag, list);
    }
  }

  const sections: SectionDef[] = [];
  for (const tag of tagOrder) {
    const endpoints = sectionMap.get(tag);
    if (endpoints?.length) sections.push({ title: tag, endpoints });
  }
  for (const [tag, endpoints] of sectionMap) {
    if (!tagOrder.includes(tag)) sections.push({ title: tag, endpoints });
  }
  return sections;
}
