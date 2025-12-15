import { cn } from './cn';
export function Card({className,...props}:React.HTMLAttributes<HTMLDivElement>){return <div className={cn('rounded-2xl border border-border bg-card shadow-soft',className)} {...props}/>}
