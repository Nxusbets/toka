export default function LoadingSpinner({ size = 40 }: { size?: number }) {
  return (
    <div className="loading-spinner-container">
      <div
        className="loading-spinner"
        style={{ width: size, height: size }}
      />
    </div>
  );
}
