const YEAR = new Date().getFullYear()

export function Footer() {
  return (
    <footer className="relative mt-20 px-6 py-10 font-display text-sm text-muted-foreground before:absolute before:top-0 before:left-1/2 before:h-px before:w-full before:max-w-6xl before:-translate-x-1/2 before:bg-amber-600 before:opacity-10 before:[mask-image:linear-gradient(90deg,transparent_0%,black_40%,black_60%,transparent_100%)] sm:px-12 dark:before:bg-orange-300">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <span className="font-brand text-base text-foreground">NoteNest</span>
        <span>A community library of academic notes.</span>
      </div>
      <div className="mx-auto mt-4 flex max-w-6xl flex-col gap-1 border-t border-card-edge pt-4 text-xs sm:flex-row sm:items-center sm:justify-between">
        <span>
          Made by{' '}
          <span className="font-medium text-foreground">Hiresh Yadav</span>
        </span>
        <span>© {YEAR} NoteNest. All rights reserved.</span>
      </div>
    </footer>
  )
}
