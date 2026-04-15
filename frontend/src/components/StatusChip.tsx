type StatusChipProps = {
  children: string;
  tone?: 'aqua' | 'amber' | 'slate';
};

const toneClasses: Record<NonNullable<StatusChipProps['tone']>, string> = {
  aqua: 'border-aurora-500/30 bg-aurora-500/10 text-aurora-500',
  amber: 'border-ember-400/30 bg-ember-400/10 text-ember-400',
  slate: 'border-white/15 bg-white/5 text-slate-200',
};

export function StatusChip({ children, tone = 'slate' }: StatusChipProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.22em] ${toneClasses[tone]}`}>
      {children}
    </span>
  );
}
