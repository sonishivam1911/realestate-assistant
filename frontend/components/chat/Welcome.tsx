import styles from "./Welcome.module.css";

const EXAMPLES = [
  "Value 199 Hyde Park, Somerset NJ 08873 — 2bd/3ba townhouse, 1400 sqft",
  "CMA for 742 Evergreen Terrace, Springfield — single family, 3bd/2ba, 1850 sqft",
  "What's the market like within 5 miles of 78701 Austin TX?",
];

type Props = {
  onExample: (text: string) => void;
  hasEmail: boolean;
  emailDeliveryEnabled: boolean;
  onOpenSettings: () => void;
};

export function Welcome({
  onExample,
  hasEmail,
  emailDeliveryEnabled,
  onOpenSettings,
}: Props) {
  const needsEmail = emailDeliveryEnabled && !hasEmail;

  return (
    <div className={styles.welcome}>
      <h2>Consumer Market Analysis</h2>
      <p className={styles.sub}>
        {needsEmail ? (
          <>
            Add your email in{" "}
            <button type="button" className={styles.link} onClick={onOpenSettings}>
              Settings
            </button>{" "}
            to receive reports by email, then ask for a property valuation.
          </>
        ) : emailDeliveryEnabled ? (
          "Ask for a CMA — sold comps (3 mo), cited sources, full report to your inbox."
        ) : (
          "Ask for a CMA — sold comps (3 mo) and cited sources. Enable email delivery in Settings anytime."
        )}
      </p>
      {!needsEmail && (
        <div className={styles.examples}>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              className={styles.example}
              onClick={() => onExample(ex)}
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
