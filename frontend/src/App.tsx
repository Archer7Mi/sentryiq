import { MetricCard } from './components/MetricCard';
import { StatusChip } from './components/StatusChip';
import { humanRisk, metrics, queue, stackSteps } from './lib/demoData';

function App() {
  return (
    <main className="relative min-h-screen overflow-hidden text-slate-100">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(77,214,194,0.18),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(227,140,43,0.18),_transparent_28%),linear-gradient(180deg,_rgba(4,8,22,1)_0%,_rgba(7,17,31,1)_48%,_rgba(3,8,16,1)_100%)]" />
      <div className="absolute left-1/2 top-0 h-80 w-80 -translate-x-1/2 rounded-full bg-aurora-500/10 blur-3xl" />

      <section className="relative mx-auto max-w-7xl px-6 py-10 sm:px-8 lg:px-10 lg:py-14">
        <div className="flex flex-wrap items-center gap-3">
          <StatusChip tone="aqua">SentryIQ</StatusChip>
          <StatusChip tone="amber">Technical Shield + Human Shield</StatusChip>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div className="max-w-3xl">
            <p className="text-sm uppercase tracking-[0.4em] text-slate-400">AI-powered SMB security platform</p>
            <h1 className="mt-5 text-5xl font-semibold tracking-tight text-white sm:text-6xl">
              Detect, prioritize, and explain cyber risk in plain English.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              SentryIQ combines vulnerability intelligence, chain detection, and social-engineering simulation in one
              demo-ready workspace for SMB operators who need action, not alert fatigue.
            </p>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/6 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Demo status</p>
            <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
              <p>Stack wizard scaffolded.</p>
              <p>CVE and KEV intake hooks ready.</p>
              <p>Chain reasoning and phishing copy placeholders are in place.</p>
              <p>Frontend and backend are wired for the first build pass.</p>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              <a className="rounded-full bg-white px-4 py-2 text-sm font-medium text-ink-950 transition hover:opacity-90" href="#priority">
                View priority queue
              </a>
              <a className="rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-white transition hover:border-white/30" href="#risk">
                View human risk
              </a>
            </div>
          </div>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} label={metric.label} value={metric.value} detail={metric.detail} />
          ))}
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Stack wizard</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Guided onboarding for the SMB environment</h2>
            <div className="mt-6 space-y-4">
              {stackSteps.map((step, index) => (
                <div key={step} className="flex gap-4 rounded-2xl border border-white/10 bg-black/10 p-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-aurora-500/15 text-sm font-semibold text-aurora-500">
                    0{index + 1}
                  </div>
                  <p className="text-sm leading-6 text-slate-300">{step}</p>
                </div>
              ))}
            </div>
          </section>

          <section id="priority" className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Priority queue</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Patch first, explain second</h2>
            <div className="mt-6 space-y-4">
              {queue.map((item, index) => (
                <div key={item.title} className="rounded-2xl border border-white/10 bg-black/10 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Rank {index + 1}</p>
                      <h3 className="mt-1 text-base font-semibold text-white">{item.title}</h3>
                    </div>
                    <span className="rounded-full border border-ember-400/30 bg-ember-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-ember-400">
                      {item.score}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{item.reason}</p>
                  <p className="mt-2 text-sm leading-6 text-aurora-500">{item.action}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Chain detection</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">How isolated findings become a critical path</h2>
            <div className="mt-5 rounded-2xl border border-white/10 bg-black/10 p-5 text-sm leading-7 text-slate-300">
              Apache HTTP Server plus OpenSSL creates a reachable chain from a public service into a deeper execution path.
              The combined risk jumps above the individual CVSS scores, so the model escalates the patch order.
            </div>
          </section>

          <section id="risk" className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Human risk</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Employee coaching based on simulation performance</h2>
            <div className="mt-5 space-y-4">
              {humanRisk.map((person) => (
                <div key={person.employee} className="rounded-2xl border border-white/10 bg-black/10 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-base font-semibold text-white">{person.employee}</h3>
                      <p className="text-sm text-slate-400">{person.role}</p>
                    </div>
                    <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-slate-200">
                      Score {person.score}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{person.coaching}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;
