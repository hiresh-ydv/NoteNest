import { Button } from '../components/Button.jsx'

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl py-16 text-center">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        404
      </p>
      <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight text-foreground">
        Page not found
      </h1>
      <p className="mt-3 text-sm text-muted-foreground">
        The page you were looking for does not exist.
      </p>
      <Button to="/" className="mt-6">
        Back to explore
      </Button>
    </div>
  )
}
