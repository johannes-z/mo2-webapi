interface BaseUrlInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function BaseUrlInput({ value, onChange }: BaseUrlInputProps) {
  return (
    <p className="base-url-row">
      Base URL:{" "}
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="http://localhost:5000"
        aria-label="API base URL"
      />
    </p>
  );
}
