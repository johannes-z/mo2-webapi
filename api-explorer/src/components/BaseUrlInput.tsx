interface BaseUrlInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function BaseUrlInput({ value, onChange }: BaseUrlInputProps) {
  return (
    <div className="flex items-center gap-2 mb-6 text-sm text-muted">
      Base URL:{" "}
      <input
        type="text"
        className="flex-1 max-w-[320px] py-1.5 px-2.5 bg-surface border border-border rounded-md text-text font-mono text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="http://localhost:5000"
        aria-label="API base URL"
      />
    </div>
  );
}
