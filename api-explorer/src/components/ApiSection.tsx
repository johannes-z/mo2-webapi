import type { SectionDef } from "../data/endpoints";
import { EndpointCard } from "./EndpointCard";

interface ApiSectionProps {
  section: SectionDef;
  baseUrl: string;
}

export function ApiSection({ section, baseUrl }: ApiSectionProps) {
  return (
    <>
      <p className="section-title">{section.title}</p>
      {section.endpoints.map((ep) => (
        <EndpointCard key={`${ep.method} ${ep.path}`} endpoint={ep} baseUrl={baseUrl} />
      ))}
    </>
  );
}
