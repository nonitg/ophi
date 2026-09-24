import { WaitlistForm } from "@/components/waitlist-form";
import { ToothScene } from "@/components/tooth-scene";
import { InfoPanel } from "@/components/info-panel";
import { JsonLd } from "@/components/json-ld";
import Link from "next/link";
import { Icon } from "@/components/icons";
import { CopyEmail } from "@/components/copy-email";
import { pill, pillIcon, pillTag } from "@/components/pill";
import { copy } from "@/lib/copy";

export default function Page() {
  return (
    <div className="site-shell mx-auto flex min-h-svh w-[min(calc(100%-112px),1400px)] flex-col tablet:w-[calc(100%-72px)] phone:w-[calc(100%-40px)] small:w-[calc(100%-32px)]" id="top">
      <a className="fixed -top-[100px] left-5 z-50 bg-ink p-[15px] text-paper focus:top-[15px]" href="#main">Skip to content</a>
      <header className="site-header flex h-[98px] flex-none items-center justify-between phone:h-[84px]">
        <Link className="inline-block pr-[7px] text-[46px] leading-none font-[650] tracking-[-3.7px] phone:text-[38px] phone:tracking-[-3px]" href="/" aria-label="Ophi home">ophi<span className="text-rust xray:text-white xray:[text-shadow:0_0_14px_#dff3e6a6]" aria-hidden="true">.</span></Link>
        <div className="header-tools flex items-center gap-5 phone:gap-3.5">
          {/* ToothScene fills this with the X-ray control once the tooth is live. */}
          <div id="xray-slot" className="xray-slot relative flex" />
        </div>
      </header>
      <main id="main" className="flex-1">
        {/* A single editorial composition: type and sculpture occupy the same space. */}
        <section className="poster relative isolate h-[clamp(430px,53svh,610px)] wide:h-[clamp(540px,52svh,650px)] tablet:h-[clamp(355px,48svh,460px)] phone:mt-1.5 phone:mb-8 phone:h-[405px] phablet:h-[460px] small:h-[375px]" aria-labelledby="poster-title">
          {/* In X-ray the headline turns radiopaque (components/xray-filters.tsx) and adds to the tooth wherever the two
              overlap, as superimposed structures do on a radiograph. The density filter reads a solid highlight as mass
              and buries the glyphs, so filtered type selects faintly (here and on the footer wordmark). */}
          <h1 id="poster-title" className="poster-title pointer-events-none absolute inset-[20px_0_0] z-2 flex flex-col justify-between text-[length:clamp(96px,11.2vw,174px)] leading-[.98] tracking-[-.065em] tablet:text-[11.6vw] phone:inset-[3px_0_0] phone:text-[length:clamp(64px,15.4vw,105px)] phone:leading-none phone:tracking-[-.06em] small:text-[60px] motion-safe:animate-[arrive_.75s_ease-out_both] xray:mix-blend-screen xray:[filter:url(#xray-density)] xray:selection:bg-[#e6ece32e] xray:supports-[mix-blend-mode:plus-lighter]:mix-blend-plus-lighter">
            <span className="block pt-4.5 phone:pt-0">Good care.</span>
            {/* “Less” over “paperwork.” at every phone width; the X-ray note sits beside “Less” (tooth-scene.tsx). */}
            <em className="block self-end pb-[3px] text-[.98em] tracking-[-.065em] phone:w-min phone:max-w-full phone:self-start phone:pb-0 phone:text-[.86em] phone:leading-[.99]">Less paperwork.</em>
          </h1>
          <div className="sculpture absolute -top-[8%] -right-[2%] z-1 h-[103%] w-[53%] wide:-top-[5%] wide:w-[55%] tablet:-top-[4%] tablet:h-[105%] tablet:w-[55%] phone:top-[6%] phone:right-0 phone:h-[88%] phone:w-full phablet:top-[5%] phablet:right-0 phablet:w-[84%] small:top-[8%] motion-safe:animate-[arrive_1s_.08s_ease-out_both]">
            <div className="pointer-events-none absolute top-1/4 left-[14%] h-[51%] w-[75%] -rotate-31 rounded-[50%] border border-[#c1ccb5] phone:left-[10%] phone:h-1/2 phone:w-[80%] xray:border-[#e6ece333]" aria-hidden="true" />
            <ToothScene />
          </div>
        </section>
        {/* The signup band: one sage panel for the one action. Two columns share rows, so "Why Ophi?" lines up with the email field.
            Stacked on phones, the rows no longer need to line up, and a grid track would size to the widest control.
            The introduction follows the headline on bare paper, so the band holds the signup alone. */}
        <div className="entry-row my-9 grid grid-cols-[minmax(0,1fr)_minmax(0,490px)] grid-rows-[auto_auto] gap-x-[6%] rounded-[36px] bg-sage p-11 tablet:grid-cols-[minmax(0,1fr)_minmax(0,440px)] phone:mt-0 phone:mb-8 phone:flex phone:flex-col phone:gap-[30px] phone:rounded-none phone:bg-transparent phone:p-0">
          <div className="introduction row-span-2 grid grid-rows-subgrid phone:flex phone:flex-col phone:gap-4.5">
            {/* Short lines end on a pair of words, not one (text-pretty on phones, here and below). */}
            <p className="max-w-[400px] pt-0.5 text-[17px] leading-[1.6] text-[#55624e] tablet:text-[15px] phone:max-w-[340px] phone:pt-0 phone:text-[16px] phone:leading-[1.55] phone:text-pretty xray:text-[#c3cfc4]">We’re building for dental teams who’d rather spend their time on people.</p>
            <div className="introduction-actions flex min-h-[58px] items-center self-start phone:min-h-0"><InfoPanel kind="why" /></div>
          </div>
          <section id="join" className="signup row-span-2 grid grid-rows-subgrid phone:block phone:rounded-[28px] phone:bg-sage phone:px-5 phone:pt-[26px] phone:pb-6" aria-labelledby="signup-title">
            <div className="signup-head">
              <h2 id="signup-title" className="text-[28px] leading-[1.15] tracking-[-.7px] phone:text-[25px] small:text-[23px]">Be here from the beginning.</h2>
              <p className="signup-note mt-2.5 mb-4.5 text-[13px] leading-[1.6] text-muted phone:text-pretty">Get occasional updates and hear when Ophi is ready.</p>
            </div>
            <WaitlistForm />
          </section>
        </div>
        {/* Answers start where the form starts and end at the card edge: form track plus card padding.
            Contact follows the questions in reading order; wide screens tuck it under the heading. */}
        <section className="faq grid grid-cols-[minmax(0,1fr)_minmax(0,534px)] grid-rows-[auto_1fr] gap-x-[6%] border-t border-line pt-7 pb-9 [box-shadow:var(--crease)] [grid-template-areas:'head_items'_'contact_items'] tablet:grid-cols-[minmax(0,1fr)_minmax(0,484px)] phone:grid-cols-[1fr] phone:grid-rows-none phone:gap-3.5 phone:pt-[25px] phone:pb-7 phone:[grid-template-areas:'head'_'items'_'contact']" aria-labelledby="faq-title">
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
