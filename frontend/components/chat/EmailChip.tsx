import styles from "./EmailChip.module.css";

type Props = {
  email: string;
  onEdit: () => void;
  disabled?: boolean;
};

export function EmailChip({ email, onEdit, disabled }: Props) {
  return (
    <button
      type="button"
      className={styles.chip}
      onClick={onEdit}
      disabled={disabled}
      title="Change email"
    >
      <span className={styles.dot} aria-hidden />
      <span className={styles.label}>Reports to</span>
      <span className={styles.email}>{email}</span>
    </button>
  );
}
