interface MatchControlProps {
  onRun: () => void;
  busy: boolean;
  disabled: boolean;
}

export function MatchControl({ onRun, busy, disabled }: MatchControlProps) {
  return (
    <button
      type="button"
      className={disabled || busy ? "run run-idle" : "run run-go"}
      onClick={onRun}
      disabled={disabled}
      aria-disabled={busy}
      aria-busy={busy}
    >
      {busy ? "Finding matches" : "Find matches"}
    </button>
  );
}
