import { FormEvent, useEffect, useState } from "react";
import { isValidEmail } from "@/lib/emailStorage";
import {
  loadSettings,
  saveSettings,
  type UserSettings,
  validateSettings,
} from "@/lib/settingsStorage";
import styles from "./SettingsPanel.module.css";

type Props = {
  onSave?: (settings: UserSettings) => void;
  externalError?: string | null;
};

export function SettingsPanel({ onSave, externalError }: Props) {
  const [email, setEmail] = useState("");
  const [emailDeliveryEnabled, setEmailDeliveryEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const s = loadSettings();
    setEmail(s.email);
    setEmailDeliveryEnabled(s.emailDeliveryEnabled);
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const settings: UserSettings = {
      email: email.trim(),
      emailDeliveryEnabled,
    };
    const validationError = validateSettings(settings);
    if (validationError) {
      setError(validationError);
      setSaved(false);
      return;
    }
    saveSettings(settings);
    setError(null);
    setSaved(true);
    onSave?.(settings);
    window.setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className={styles.panel}>
      <div className={styles.card}>
        <h2 className={styles.title}>Settings</h2>
        <p className={styles.subtitle}>
          Configure where your CMA reports are delivered after each analysis.
        </p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label htmlFor="settings-email">Email address</label>
            <input
              id="settings-email"
              type="email"
              className={styles.input}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError(null);
                setSaved(false);
              }}
              autoComplete="email"
            />
          </div>

          <label className={styles.toggleRow}>
            <span className={styles.toggleText}>
              <strong>Email me chat reports</strong>
              <span>
                Send the full CMA report to your inbox when analysis finishes
              </span>
            </span>
            <input
              type="checkbox"
              className={styles.toggle}
              checked={emailDeliveryEnabled}
              onChange={(e) => {
                setEmailDeliveryEnabled(e.target.checked);
                setError(null);
                setSaved(false);
              }}
            />
          </label>

          {emailDeliveryEnabled && !isValidEmail(email) && email.length > 0 && (
            <p className={styles.warn}>
              Enter a valid email address to receive reports.
            </p>
          )}

          {error && <p className={styles.error}>{error}</p>}
          {externalError && !error && (
            <p className={styles.error}>{externalError}</p>
          )}
          {saved && <p className={styles.success}>Settings saved.</p>}

          <button type="submit" className={styles.save}>
            Save settings
          </button>
        </form>

        <p className={styles.note}>
          Reports are sent via SMTP configured on the server. If delivery is
          off, you can still chat and copy results from the conversation.
        </p>
      </div>
    </div>
  );
}
