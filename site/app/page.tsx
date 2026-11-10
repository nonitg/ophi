import { WaitlistForm } from "@/components/waitlist-form";
import { ToothScene } from "@/components/tooth-scene";
import { InfoPanel } from "@/components/info-panel";
import { JsonLd } from "@/components/json-ld";
import Link from "next/link";
import { Icon } from "@/components/icons";
import { CopyEmail } from "@/components/copy-email";
import { CallPlayer } from "@/components/call-player";
import { HearIt } from "@/components/hear-it";
import { ApprovalCard } from "@/components/approval-card";
import { pill, pillIcon, pillTag, primaryPill } from "@/components/pill";
import { copy } from "@/lib/copy";
import { demoCall, moment, recordedOn, recordings } from "@/lib/calls";

// Section headings echo the poster: display serif, the closing words in italic and stepped to the right.
const sectionTitle = "text-[length:clamp(40px,4.7vw,68px)] leading-[1.02] tracking-[-.045em] phone:text-[length:clamp(33px,9.6vw,42px)] phone:leading-[1.05]";
const section = "mt-[clamp(72px,8.5vw,128px)] border-t border-line pt-9 [box-shadow:var(--crease)] phone:mt-16 phone:pt-7";
const row = "border-t border-line [box-shadow:var(--crease)]";

const calls = recordings.map(demoCall);
const first = recordings[0];
// Each claim about judgment carries the recorded moment that backs it, where there is one.
const judgment = copy.judgment.map((skill) => {
  const hear = skill.hear as { slug: string; tool?: string } | null;
  const recording = hear && recordings.find((r) => r.slug === hear.slug);
  const proof = recording ? moment(recording, hear.tool) : null;
  return { ...skill, proof: proof && { slug: recording!.slug, ...proof } };
});
// The request the first call left at the front desk, and the text its approval sends (wording as ophi-phone office.py).
const request = first.proposals[0];
const confirmation = `${copy.frontDesk.card.clinic}: You’re booked for a ${request.title.split(": ")[1]} on ${request.details.when}. Questions? Call ${copy.frontDesk.card.phone}. Reply STOP to opt out.`;

export default function Page() {
  return (
    <div className="site-shell mx-auto flex min-h-svh w-[min(calc(100%-112px),1400px)] flex-col tablet:w-[calc(100%-72px)] phone:w-[calc(100%-40px)] small:w-[calc(100%-32px)]" id="top">
      <a className="fixed -top-[100px] left-5 z-50 bg-ink p-[15px] text-paper focus:top-[15px]" href="#main">Skip to content</a>
      <header className="site-header flex h-[98px] flex-none items-center justify-between phone:h-[84px]">
        <Link className="inline-block pr-[7px] text-[46px] leading-none font-[650] tracking-[-3.7px] phone:text-[38px] phone:tracking-[-3px]" href="/" aria-label="Ophi home">ophi<span className="text-rust xray:text-white xray:[text-shadow:0_0_14px_#dff3e6a6]" aria-hidden="true">.</span></Link>
        <div className="header-tools flex items-center gap-5 phone:gap-3.5">
          <nav className="flex items-center max-[940px]:hidden" aria-label="On this page">
            {copy.nav.map(({ href, label }) => <a key={href} href={href} className="rounded-full px-3 py-2 text-[13px] text-ink-soft transition-[background,color] duration-200 hover:bg-field hover:text-ink">{label}</a>)}
          </nav>
          {/* ToothScene fills this with the X-ray control once the tooth is live. */}
          <div id="xray-slot" className="xray-slot relative flex" />
          <a className={pill({ size: "footer", className: "header-cta phone:hidden" })} href="#join">{copy.cta}<span className={pillTag({ size: "footer" })}><Icon name="arrow" className={`${pillIcon} group-hover/pill:translate-x-px group-hover/pill:-translate-y-px`} /></span></a>
        </div>
      </header>
      <main id="main" className="flex-1">
        {/* A single editorial composition: type and sculpture occupy the same space. */}
        <section className="poster relative isolate h-[clamp(430px,53svh,610px)] wide:h-[clamp(540px,52svh,650px)] tablet:h-[clamp(355px,48svh,460px)] phone:mt-1.5 phone:mb-8 phone:h-[405px] phablet:h-[460px] small:h-[375px]" aria-labelledby="poster-title">
          {/* In X-ray the headline turns radiopaque (components/xray-filters.tsx) and adds to the tooth wherever the two
              overlap, as superimposed structures do on a radiograph. The density filter reads a solid highlight as mass
              and buries the glyphs, so filtered type selects faintly (here and on the footer wordmark). */}
          <h1 id="poster-title" className="poster-title pointer-events-none absolute inset-[20px_0_0] z-2 flex flex-col justify-between text-[length:clamp(96px,11.2vw,174px)] leading-[.98] tracking-[-.065em] tablet:text-[11.6vw] phone:inset-[3px_0_0] phone:text-[length:clamp(64px,15.4vw,105px)] phone:leading-none phone:tracking-[-.06em] small:text-[60px] motion-safe:animate-[arrive_.75s_ease-out_both] xray:mix-blend-screen xray:[filter:url(#xray-density)] xray:selection:bg-[#e6ece32e] xray:supports-[mix-blend-mode:plus-lighter]:mix-blend-plus-lighter">
            <span className="block pt-4.5 phone:pt-0">Patient calls.</span>
            {/* "Always" over "answered." at every phone width; the X-ray note sits beside "Always" (tooth-scene.tsx). */}
            <em className="block self-end pb-[3px] text-[.98em] tracking-[-.065em] phone:w-min phone:max-w-full phone:self-start phone:pb-0 phone:text-[.86em] phone:leading-[.99]">Always answered.</em>
          </h1>
          <div className="sculpture absolute -top-[8%] -right-[2%] z-1 h-[103%] w-[53%] wide:-top-[5%] wide:w-[55%] tablet:-top-[4%] tablet:h-[105%] tablet:w-[55%] phone:top-[6%] phone:right-0 phone:h-[88%] phone:w-full phablet:top-[5%] phablet:right-0 phablet:w-[84%] small:top-[8%] motion-safe:animate-[arrive_1s_.08s_ease-out_both]">
            <div className="pointer-events-none absolute top-1/4 left-[14%] h-[51%] w-[75%] -rotate-31 rounded-[50%] border border-[#c1ccb5] phone:left-[10%] phone:h-1/2 phone:w-[80%] xray:border-[#e6ece333]" aria-hidden="true" />
            <ToothScene />
          </div>
        </section>
        {/* What it is and the two things to do next: ask for access, or hear it first. */}
        <div className="standfirst grid grid-cols-[minmax(0,1fr)_auto] items-end gap-x-[6%] gap-y-7 pt-9 pb-11 tablet:pt-7 phone:grid-cols-1 phone:pt-0 phone:pb-9">
          <p className="max-w-[640px] font-serif text-[length:clamp(23px,2.05vw,30px)] leading-[1.3] tracking-[-.02em] text-pretty phone:text-[22px]">{copy.standfirst}</p>
          <div className="grid justify-items-end gap-3.5 phone:justify-items-start">
            <div className="flex flex-wrap items-center gap-2.5">
              <a className={`group/join ${primaryPill}`} href="#join">{copy.cta}<Icon name="arrow" className="size-[22px] transition-transform duration-350 ease-out group-hover/join:translate-x-0.5 group-hover/join:-translate-y-0.5" /></a>
              <HearIt slug={first.slug} t={0} label={copy.listen.action} show />
            </div>
            <p className="flex items-center gap-2 text-[12px] leading-[1.5] text-muted"><span className="size-1.5 flex-none rounded-full bg-orange" aria-hidden="true" />{copy.status}</p>
          </div>
        </div>
        {/* The listening room: the one sage panel above the fold's edge. Proof before any claim. */}
        <section id="listen" className="listen scroll-mt-6 rounded-[36px] bg-sage p-11 tablet:p-8 phone:-mx-2.5 phone:rounded-[28px] phone:px-4 phone:pt-7 phone:pb-5" aria-labelledby="listen-title">
          <CallPlayer calls={calls} note={copy.listen.note.replace("{date}", recordedOn(first))} />
        </section>
        <section id="judgment" className={`${section} scroll-mt-6`} aria-labelledby="judgment-title">
          <h2 id="judgment-title" className={sectionTitle}><span className="block text-balance">The hard part isn’t the voice.</span><em className="block pl-[16%] phone:pl-0">It’s the judgment.</em></h2>
          <ul className="mt-14 phone:mt-9">
            {judgment.map(({ title, body, proof }) => (
              <li key={title} className={`${row} grid grid-cols-[minmax(0,5fr)_minmax(0,6fr)_152px] items-start gap-x-[5%] gap-y-3 py-7 tablet:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] phone:grid-cols-1 phone:py-6`}>
                <h3 className="font-serif text-[length:clamp(25px,2.2vw,31px)] leading-[1.15] tracking-[-.02em] text-pretty">{title}</h3>
                <div className="max-w-[540px]">
                  <p className="text-[15px] leading-[1.65] text-ink-soft">{body}</p>
                  {/* Ophi's own words from the recording, not ours: what it said, or the note a transfer left the team. */}
                  {proof && <p className="mt-3 line-clamp-2 font-serif text-[17px] leading-[1.45] text-muted italic phone:line-clamp-3">{proof.note ? <><span className="font-sans text-[13px] not-italic">{copy.listen.teamNote}</span> “{proof.note}”</> : <>“{proof.quote}”</>}</p>}
                </div>
                <div className="flex justify-end tablet:col-start-2 tablet:justify-start phone:col-start-1">
                  {proof && <HearIt slug={proof.slug} t={proof.t} label="Hear it" about={title} />}
                </div>
              </li>
            ))}
          </ul>
        </section>
        <section id="front-desk" className={`${section} scroll-mt-6`} aria-labelledby="front-desk-title">
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,500px)] items-start gap-x-[8%] gap-y-12 tablet:grid-cols-1">
            <div>
              <h2 id="front-desk-title" className={sectionTitle}>Ophi asks.<em className="block pl-[14%] phone:pl-0">Your team says yes.</em></h2>
              <p className="mt-9 max-w-[500px] text-[17px] leading-[1.6] text-ink-soft phone:mt-6 phone:text-[16px]">{copy.frontDesk.lede}</p>
              <ol className="mt-9 max-w-[560px] phone:mt-7">
                {copy.frontDesk.steps.map(({ title, body }, i) => (
                  <li key={title} className={`${row} grid grid-cols-[44px_minmax(0,1fr)] py-4.5`}>
                    <span className="font-serif text-[22px] leading-[1.2] text-muted italic" aria-hidden="true">{i + 1}</span>
                    <div><h3 className="font-sans text-[14px] leading-[1.5] font-medium">{title}</h3><p className="mt-1 text-[14px] leading-[1.6] text-muted">{body}</p></div>
                  </li>
                ))}
              </ol>
            </div>
            <ApprovalCard proposal={request} text={confirmation} />
          </div>
          <div className={`${row} mt-16 grid grid-cols-[minmax(0,5fr)_minmax(0,6fr)_152px] items-start gap-x-[5%] gap-y-3 py-7 tablet:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] phone:mt-12 phone:grid-cols-1 phone:py-6`}>
            <h3 className="font-serif text-[length:clamp(25px,2.2vw,31px)] leading-[1.15] tracking-[-.02em] text-pretty">{copy.frontDesk.software.title}</h3>
            <p className="max-w-[540px] text-[15px] leading-[1.65] text-ink-soft">{copy.frontDesk.software.body}</p>
          </div>
        </section>
        <section className={section} aria-labelledby="limits-title">
          <h2 id="limits-title" className={sectionTitle}>What Ophi <em>won’t do.</em></h2>
          <ul className="mt-12 grid grid-cols-2 gap-x-[8%] phone:mt-8 phone:grid-cols-1">
            {copy.limits.map(({ title, body }) => (
              <li key={title} className={`${row} flex gap-4.5 py-6`}>
                <span className="mt-1 grid size-8 flex-none place-items-center rounded-full bg-sage text-label xray:text-ink-soft" aria-hidden="true"><Icon name="close" className="size-[15px]" /></span>
                <div><h3 className="font-serif text-[length:clamp(23px,1.9vw,27px)] leading-[1.2] tracking-[-.02em]">{title}</h3><p className="mt-1.5 max-w-[440px] text-[14.5px] leading-[1.65] text-ink-soft">{body}</p></div>
              </li>
            ))}
          </ul>
        </section>
        {/* The signup band: one sage panel for the one action. Two columns share rows, so "Why Ophi?" lines up with the email field.
            Stacked on phones, the rows no longer need to line up, and a grid track would size to the widest control.
            The introduction follows on bare paper, so the band holds the signup alone. */}
        <div className="entry-row mt-[clamp(72px,8.5vw,128px)] mb-9 grid grid-cols-[minmax(0,1fr)_minmax(0,490px)] grid-rows-[auto_auto] gap-x-[6%] rounded-[36px] bg-sage p-11 tablet:grid-cols-[minmax(0,1fr)_minmax(0,440px)] phone:mt-16 phone:mb-8 phone:flex phone:flex-col phone:gap-[30px] phone:rounded-none phone:bg-transparent phone:p-0">
          <div className="introduction row-span-2 grid grid-rows-subgrid phone:flex phone:flex-col phone:gap-4.5">
            {/* Short lines end on a pair of words, not one (text-pretty on phones, here and below). */}
            <p className="max-w-[400px] pt-0.5 text-[17px] leading-[1.6] text-[#55624e] tablet:text-[15px] phone:max-w-[340px] phone:pt-0 phone:text-[16px] phone:leading-[1.55] phone:text-pretty xray:text-[#c3cfc4]">{copy.signup.intro}</p>
            <div className="introduction-actions flex min-h-[58px] items-center self-start phone:min-h-0"><InfoPanel kind="why" /></div>
          </div>
          <section id="join" className="signup row-span-2 grid scroll-mt-6 grid-rows-subgrid phone:block phone:rounded-[28px] phone:bg-sage phone:px-5 phone:pt-[26px] phone:pb-6" aria-labelledby="signup-title">
            <div className="signup-head">
              <h2 id="signup-title" className="text-[28px] leading-[1.15] tracking-[-.7px] phone:text-[25px] small:text-[23px]">{copy.signup.title}</h2>
              <p className="signup-note mt-2.5 mb-4.5 text-[13px] leading-[1.6] text-muted phone:text-pretty">{copy.signup.note}</p>
            </div>
            <WaitlistForm />
          </section>
        </div>
        {/* Answers start where the form starts and end at the card edge: form track plus card padding.
            Contact follows the questions in reading order; wide screens tuck it under the heading. */}
        <section id="questions" className="faq grid scroll-mt-6 grid-cols-[minmax(0,1fr)_minmax(0,534px)] grid-rows-[auto_1fr] gap-x-[6%] border-t border-line pt-7 pb-9 [box-shadow:var(--crease)] [grid-template-areas:'head_items'_'contact_items'] tablet:grid-cols-[minmax(0,1fr)_minmax(0,484px)] phone:grid-cols-[1fr] phone:grid-rows-none phone:gap-3.5 phone:pt-[25px] phone:pb-7 phone:[grid-template-areas:'head'_'items'_'contact']" aria-labelledby="faq-title">
          <div className="[grid-area:head]">
            <h2 id="faq-title" className="text-[28px] leading-[1.2] tracking-[-.7px] phone:text-[25px]">A few quick answers.</h2>
          </div>
          {/* Relative keeps the questions above the copy pill where it overflows its narrow column (701–770px). */}
          <div className="faq-items relative [grid-area:items]">
            {copy.faq.map(({ q, a }) => (
              // Answers ease open instead of snapping; browsers without interpolate-size get the fade only.
              <details key={q} className="group/faq border-line not-first:border-t motion-safe:[interpolate-size:allow-keywords] motion-safe:details-content:overflow-hidden motion-safe:details-content:[block-size:0] motion-safe:details-content:[transition:block-size_.4s_var(--ease-out),content-visibility_.4s_allow-discrete] motion-safe:open:details-content:[block-size:auto]">
                <summary className="flex min-h-12 list-none items-center justify-between gap-4 py-3 text-[13px]">{q}<Icon name="plus" className="size-[18px] flex-none transition-transform duration-350 ease-out group-open/faq:rotate-45" /></summary>
                <p className="pr-6 pb-4 text-[13px] leading-[1.7] text-muted phone:text-pretty motion-safe:-translate-y-1 motion-safe:opacity-0 motion-safe:[transition:opacity_.25s_ease-out,translate_.4s_var(--ease-out)] motion-safe:group-open/faq:translate-y-0 motion-safe:group-open/faq:opacity-100 motion-safe:group-open/faq:delay-60">{a}</p>
              </details>
            ))}
          </div>
          {/* Contact lives with the questions, keeping the signup band to one action. */}
          <div className="contact mt-[26px] grid gap-2.5 self-start text-[13px] text-muted [grid-area:contact] phone:mt-3.5">
            <p>Anything else? Write to us.</p>
            <CopyEmail email={copy.contactEmail} />
          </div>
        </section>
      </main>
      <footer className="site-footer mt-auto border-t border-line pt-9 text-muted [box-shadow:var(--crease)] phone:pt-5">
        {/* Decorative; its oversized glyph box overlaps the contact row above and would swallow clicks. */}
        {/* The wordmark spans the footer edge to edge; its size tracks the footer's width. */}
        <div className="footer-wordmark @container pointer-events-none flex items-center pb-[38px] leading-[1.05] font-semibold text-ink phone:pt-[13px] phone:pb-[25px]" aria-hidden="true"><span className="-ml-[.05em] text-[length:52cqw] tracking-[-.085em] xray:[filter:url(#xray-density)] xray:selection:bg-[#e6ece32e]">ophi<span className="text-rust">.</span></span></div>
        {/* Phones: privacy left, a round back-to-top right, copyright last. */}
        <div className="footer-bottom flex min-h-[62px] items-center justify-between gap-6 border-t border-line text-[11px] [box-shadow:var(--crease)] phone:flex-col-reverse phone:items-start phone:gap-4 phone:pt-[18px] phone:pb-[22px] phone:text-[10px]">
          <span>© {new Date().getFullYear()} Ophi</span>
          <div className="footer-actions flex flex-wrap items-center justify-end gap-2.5 phone:w-full phone:flex-nowrap phone:justify-between">
            <InfoPanel kind="privacy" />
            <a className={pill({ size: "footer", className: "back-to-top phone:min-h-10 phone:w-10 phone:justify-center phone:p-0" })} href="#top"><span className="phone:sr-only">Back to the top</span><span className={pillTag({ size: "footer" })}><Icon name="up" className={`${pillIcon} group-hover/pill:-translate-y-0.5`} /></span></a>
          </div>
        </div>
      </footer>
      {/* Structured data for search engines: invisible, mirrors the visible copy so rich results stay honest. */}
      <JsonLd data={{ "@context": "https://schema.org", "@type": "Organization", name: copy.name, url: "https://ophi.app/", logo: "https://ophi.app/icon.svg", email: copy.contactEmail }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebSite", name: copy.name, url: "https://ophi.app/" }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "SoftwareApplication", name: copy.name, applicationCategory: "BusinessApplication", operatingSystem: "Web", description: copy.description, url: "https://ophi.app/" }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: copy.faq.map(({ q, a }) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })) }} />
    </div>
  );
}
