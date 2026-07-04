import { FormEvent, useState } from "react";
import { isValidEmail } from "@/lib/emailStorage";
import styles from "./EmailCapture.module.css";

type Props = {
  email: string;
  onSubmit: (email: string) => void;
  disabled?: boolean;
  error?: string | null;
  variant?: "inline" | "modal";
  onDismiss?: () => void;
};

export function EmailCapture({
  email,
  onSubmit,
  disabled,
  error: externalError,
  variant = "inline",
  onDismiss,
}: Props) {
  const [value, setValue] = useState(email);
  const [localError, setLocalError] = useState<string | null>(null);

  const error = externalError || localError;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!isValidEmail(trimmed)) {
      setLocalError("Enter a valid email address");
      return;
    }
    setLocalError(null);
    onSubmit(trimmed);
  };

  const card = (
    <div className={styles.card}>
      {variant === "modal" && onDismiss && (
        <button
          type="button"
          className={styles.close}
          onClick={onDismiss}
          aria-label="Close"
        >
          ×
        </button>
      )}

      <div className={styles.icon} aria-hidden>
        ✉
      </div>
      <h2 className={styles.title}>Where should we send your report?</h2>
      <p className={styles.subtitle}>
        We&apos;ll email your full CMA with comps, sources, and pricing when
        analysis finishes.
      </p>

      <form className={styles.form} onSubmit={handleSubmit}>
        <input
          type="email"
          className={`${styles.input} ${error ? styles.inputError : ""}`}
          placeholder="Email address"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setLocalError(null);
          }}
          disabled={disabled}
          autoComplete="email"
          autoFocus
        />
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" className={styles.continue} disabled={disabled}>
          Continue
        </button>
      </form>

      <p className={styles.footer}>
        Your email is only used to deliver CMA reports.
      </p>
    </div>
  );

  if (variant === "modal") {
    return (
      <div className={styles.overlay} role="dialog" aria-modal="true">
        {card}
      </div>
    );
  }

  return <div className={styles.inline}>{card}</div>;
}
