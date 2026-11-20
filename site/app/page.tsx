import Link from "next/link";
import { WaitlistForm } from "@/components/waitlist-form";
import { InfoPanel } from "@/components/info-panel";
import { JsonLd } from "@/components/json-ld";
import { Icon } from "@/components/icons";
import { CopyEmail } from "@/components/copy-email";
import { HeroStage } from "@/components/hero-stage";
import { Gap } from "@/components/gap";
import { HowThread } from "@/components/how-thread";
import { CrownStory } from "@/components/crown-story";
import { TeamView } from "@/components/team-view";
import { FrontDesk } from "@/components/front-desk";
import { SectionHead } from "@/components/section-head";
import { Reveal } from "@/components/reveal";
import { SiteMenu } from "@/components/site-menu";
import { primaryPill } from "@/components/pill";
import { display, frame, heading, lede, section } from "@/components/type";
import { copy } from "@/lib/copy";

// Where Ophi is built, under the hero's buttons (or under its card in one column).
function HeroFacts({ className }: { className: string }) {
  return (
    <p className={`flex-wrap items-center gap-x-6 gap-y-2 text-[15px] text-muted motion-safe:animate-[arrive_.8s_.24s_var(--ease-out)_both] ${className}`}>
      <span className="flex items-center gap-2"><Icon name="leaf" className="size-[17px] text-orange" />{copy.madeIn}</span>
    </p>
  );
}

// One story, told in order: what Ophi is (the whole front desk), how it works, the gap it closes, one patient through
// it, the clinic's side, then the ask. Each section uses the same heading, the same card and the same thread.
export default function Page() {
  return (
    <div id="top" className="flex min-h-svh flex-col">
      <a className="fixed -top-[100px] left-5 z-50 rounded-full bg-ink px-5 py-3 text-paper focus:top-4" href="#main">Skip to content</a>
      <header className="sticky top-0 z-30 bg-paper/95 backdrop-blur-md">
        <div className={`${frame} flex h-[76px] items-center justify-between gap-6 phone:h-16`}>
          <Link className="text-[34px] leading-none font-[650] tracking-[-2.6px] phone:text-[30px]" href="/" aria-label="Ophi home" translate="no">ophi<span className="text-orange" aria-hidden="true">.</span></Link>
          <nav className="flex items-center gap-1 tablet:hidden" aria-label="On this page">
            {copy.nav.map(({ href, label }) => <a key={href} href={href} className="rounded-full px-4 py-2 text-[16px] text-ink transition-[background] duration-200 hover:bg-ink/5">{label}</a>)}
          </nav>
          <div className="flex items-center gap-2 phone:gap-1">
            <a className={`${primaryPill({ size: "lead" })} h-11 gap-3 phone:h-10 phone:px-4 phone:text-[14px]`} href="#join">{copy.cta}<Icon name="arrow" className="size-[18px] phone:hidden" /></a>
            <SiteMenu />
          </div>
        </div>
      </header>

      <main id="main" className="flex-1">
        {/* The stage keeps its full width beside the words; its light spills to the page edge and is clipped there. */}
        <section className={`${frame} grid grid-cols-[minmax(0,1fr)_minmax(0,560px)] items-center gap-x-[clamp(32px,4vw,64px)] gap-y-14 overflow-x-clip pt-[clamp(40px,6vw,96px)] tablet:grid-cols-1 phone:gap-y-10 phone:pt-8`} aria-labelledby="hero-title">
          <div>
            <h1 id="hero-title" className={`${display} motion-safe:animate-[arrive_.8s_var(--ease-out)_both]`}>{copy.hero.title}</h1>
            <p className={`${lede} mt-7 max-w-[32em] motion-safe:animate-[arrive_.8s_.1s_var(--ease-out)_both]`}>{copy.hero.lede}</p>
            {/* Side by side where they fit; a narrow phone stacks them as two full-width, thumb-sized buttons. */}
            <div className="mt-10 flex flex-wrap gap-3 motion-safe:animate-[arrive_.8s_.18s_var(--ease-out)_both] phone:mt-8 narrow:flex-col">
              <a className={`group/join ${primaryPill({ size: "lead" })} gap-4 narrow:h-13 narrow:justify-center narrow:gap-3 narrow:text-[16px]`} href="#join">{copy.cta}<Icon name="arrow" className="size-5 transition-transform duration-200 ease-(--ease-out) motion-reduce:transition-none group-hover/join:translate-x-0.5 group-hover/join:-translate-y-0.5" /></a>
              {/* A second way in for the skimmer: straight to How, which plays as it comes into view. */}
              <a href="#how" className="group/how inline-flex h-12 items-center gap-3 rounded-full border border-ink/20 py-1.5 pr-5 pl-1.5 text-[15px] text-ink [transition:background_.2s,border-color_.2s,scale_.16s_var(--ease-out)] hover:border-ink/40 hover:bg-ink/5 active:scale-[.97] narrow:h-13 narrow:justify-center narrow:pr-6 narrow:text-[16px]">
                <span className="grid size-9 place-items-center rounded-full bg-ink text-paper"><Icon name="down" className="size-4 transition-transform duration-200 ease-(--ease-out) motion-reduce:transition-none group-hover/how:translate-y-0.5" /></span>
                {copy.hero.seeHow}
              </a>
            </div>
            <HeroFacts className="mt-9 flex tablet:hidden" />
          </div>
          <div className="w-full motion-safe:animate-[arrive_1s_.2s_var(--ease-out)_both]"><HeroStage /></div>
          {/* One column: the stage comes straight after the buttons, so a phone's first screen reaches the product. */}
          <HeroFacts className="hidden tablet:flex" />
        </section>

        <section id="desk" className={`${frame} ${section}`} aria-labelledby="desk-title">
          <SectionHead id="desk-title" title={copy.desk.title} lede={copy.desk.lede} />
          <FrontDesk />
        </section>

        {/* Doors slide in from past the card's sides; clipped at the page edge so they never widen the page. */}
        <section id="how" className={`${frame} ${section} overflow-x-clip`} aria-labelledby="how-title">
          <SectionHead id="how-title" title={copy.how.title} lede={copy.how.lede} />
          <HowThread />
        </section>

        <section id="why" className={`${frame} ${section}`} aria-labelledby="why-title">
          <SectionHead id="why-title" title={copy.gap.title} lede={copy.gap.lede} />
          <Gap />
        </section>

        <section id="story" className={`${frame} ${section} tablet:px-5 phone:px-3`} aria-labelledby="story-title">
          <CrownStory />
        </section>

        <section id="clinic" className={`${frame} ${section}`} aria-labelledby="clinic-title">
          <SectionHead id="clinic-title" title={copy.team.title} lede={copy.team.lede} />
          <TeamView />
        </section>

        <section id="join" className={`${frame} ${section}`} aria-labelledby="join-title">
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,500px)] items-center gap-x-[clamp(40px,6vw,96px)] gap-y-8 rounded-[36px] bg-sage p-[clamp(32px,5vw,72px)] tablet:grid-cols-1 phone:rounded-[28px] phone:px-5 phone:py-9">
            <div>
              <h2 id="join-title" className={heading}>{copy.signup.title}</h2>
              <p className="mt-5 max-w-[30em] text-[18px] leading-[1.55] text-label">{copy.signup.note}</p>
            </div>
            <WaitlistForm />
          </div>
        </section>

        <section id="questions" className={`${frame} ${section} pb-[clamp(64px,7vw,104px)] phone:pb-16 grid grid-cols-[minmax(0,1fr)_minmax(0,640px)] gap-x-16 gap-y-10 tablet:grid-cols-1`} aria-labelledby="faq-title">
          <div>
            <h2 id="faq-title" className={heading}>{copy.faqTitle}</h2>
            <div className="mt-8 grid gap-3.5 text-[16px] text-muted tablet:hidden">
              <p>{copy.contact}</p>
              <CopyEmail email={copy.contactEmail} />
            </div>
          </div>
          <div>
            <div className="grid gap-2.5">
              {copy.faq.map(({ q, a }) => (
                // Answers ease open instead of snapping; browsers without interpolate-size get the fade only.
                <details key={q} className="group/faq rounded-[20px] bg-card shadow-[0_1px_2px_#193a300f] motion-safe:[interpolate-size:allow-keywords] motion-safe:details-content:overflow-hidden motion-safe:details-content:[block-size:0] motion-safe:details-content:[transition:block-size_.25s_var(--ease-out),content-visibility_.25s_allow-discrete] motion-safe:open:details-content:[block-size:auto]">
                  <summary className="flex min-h-[68px] list-none items-center justify-between gap-6 px-6 py-4 text-[18px] leading-[1.35] phone:px-5 phone:text-[17px]">{q}<Icon name="plus" className="size-5 flex-none transition-transform duration-200 ease-(--ease-out) motion-reduce:transition-none group-open/faq:rotate-45" /></summary>
                  <p className="px-6 pb-6 text-[16px] leading-[1.6] text-ink-soft phone:px-5">{a}</p>
                </details>
              ))}
            </div>
            <div className="mt-10 hidden gap-3.5 text-[16px] text-muted tablet:grid">
              <p>{copy.contact}</p>
              <CopyEmail email={copy.contactEmail} />
            </div>
          </div>
        </section>
      </main>

      <footer className={`${frame} text-muted`}>
        {/* Decorative: the wordmark spans the footer edge to edge; its size tracks the footer's width. */}
        <div className="@container pointer-events-none leading-[1.05] font-semibold text-ink" aria-hidden="true"><span className="-ml-[.05em] block text-[length:52cqw] tracking-[-.085em]" translate="no">ophi<span className="text-orange">.</span></span></div>
        <div className="flex min-h-[80px] flex-wrap items-center justify-between gap-4 py-5 text-[14px]">
          <span className="flex items-center gap-1.5">© {new Date().getFullYear()} Ophi<span aria-hidden="true">·</span><Icon name="leaf" className="size-4 flex-none" />{copy.madeIn}</span>
          <div className="flex flex-wrap items-center gap-2.5">
            <InfoPanel />
            <a className="inline-flex min-h-10 items-center gap-2 rounded-full px-4 text-ink hover:bg-ink/5" href="#top">Back to the top<Icon name="up" className="size-4" /></a>
          </div>
        </div>
      </footer>
      <Reveal />
      {/* Structured data for search engines: invisible, mirrors the visible copy so rich results stay honest. */}
      <JsonLd data={{ "@context": "https://schema.org", "@type": "Organization", name: copy.name, url: "https://ophi.app/", logo: "https://ophi.app/icon.svg", email: copy.contactEmail }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebSite", name: copy.name, url: "https://ophi.app/" }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "SoftwareApplication", name: copy.name, applicationCategory: "BusinessApplication", operatingSystem: "Web", description: copy.description, url: "https://ophi.app/" }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: copy.faq.map(({ q, a }) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })) }} />
    </div>
  );
}
