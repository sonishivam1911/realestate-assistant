import styles from "./Composer.module.css";

type Props = {
  input: string;
  isLoading: boolean;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  onStop: () => void;
};

export function Composer({
  input,
  isLoading,
  onInputChange,
  onSubmit,
  onStop,
}: Props) {
  return (
    <form
      className={styles.composer}
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <textarea
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        placeholder="Enter address and property details for a CMA…"
        rows={1}
        disabled={isLoading}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSubmit();
          }
        }}
      />
      {isLoading ? (
        <button type="button" className={styles.stop} onClick={onStop}>
          ■
        </button>
      ) : (
        <button type="submit" disabled={!input.trim()} className={styles.send}>
          ↑
        </button>
      )}
    </form>
  );
}
