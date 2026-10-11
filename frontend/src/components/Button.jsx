import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'

const VARIANTS = {
  solid:
    'btn-asym inline-flex h-10 items-center justify-center gap-2 bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors duration-200 hover:bg-primary/90',
  outline:
    'btn-asym-mirror inline-flex h-10 items-center justify-center gap-2 border border-card-edge bg-transparent px-4 text-sm font-medium text-foreground transition-colors duration-200 hover:border-card-edge-hover hover:bg-card-fill',
  ghost:
    'inline-flex h-10 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors duration-200 hover:text-foreground',
}

export function Button({
  variant = 'solid',
  to,
  href,
  iconRight,
  className = '',
  children,
  ...props
}) {
  const classes = `${VARIANTS[variant] ?? VARIANTS.solid} ${className}`.trim()
  const showArrow = iconRight === undefined ? variant === 'solid' : iconRight
  const content = (
    <>
      {children}
      {showArrow ? (
        <ArrowUpRight className="-ml-0.5 size-4" aria-hidden="true" />
      ) : null}
    </>
  )

  if (to) {
    return (
      <Link to={to} className={classes} {...props}>
        {content}
      </Link>
    )
  }

  if (href) {
    return (
      <a href={href} className={classes} {...props}>
        {content}
      </a>
    )
  }

  return (
    <button type="button" className={classes} {...props}>
      {content}
    </button>
  )
}
