/** Layout-preserving loading shell so the first paint matches the Operate structure. */

export function DashboardSkeleton() {
  return (
    <div className="skeleton" aria-busy="true" aria-label="Loading house load">
      <div className="skeleton__strip">
        <div className="skeleton__line skeleton__line--sm" />
        <div className="skeleton__line skeleton__line--lg" />
        <div className="skeleton__rail" />
      </div>
      <div className="skeleton__pair">
        <div className="skeleton__block" />
        <div className="skeleton__block" />
      </div>
      <div className="skeleton__table" />
    </div>
  )
}
