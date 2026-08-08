export function Button({ variant = 'primary', className = '', ...props }) {
  const variants = {
    primary: 'bg-emerald-600 text-white hover:bg-emerald-700',
    danger: 'bg-rose-600 text-white hover:bg-rose-700',
    warning: 'bg-amber-500 text-stone-950 hover:bg-amber-400',
    secondary: 'border border-stone-300 bg-white text-stone-800 hover:bg-stone-100',
  }

  return <button className={`rounded-full px-5 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`} {...props} />
}
