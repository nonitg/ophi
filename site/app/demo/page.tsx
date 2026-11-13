import type { Metadata } from "next";
import Link from "next/link";
import { leaveDetails } from "@/app/demo/actions";
import { FilmPlayer } from "@/components/film-player";
import { Icon } from "@/components/icons";
import { InfoPanel } from "@/components/info-panel";
import { pill, pillIcon, pillTag } from "@/components/pill";
import { WaitlistForm } from "@/components/waitlist-form";

const title = "Ophi: one assistant for every patient";
const description = "A 90-second film on what Ophi is building for dental clinics.";
const PHONE = { shown: "(778) 772-9034", href: "tel:+17787729034" };

// Shared by link only: nothing on the site points here, and search engines are asked to stay out.
export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: "/demo" },
  robots: { index: false, follow: false },
  openGraph: { title, description, type: "website", locale: "en_CA", url: "/demo", siteName: "Ophi", images: [{ url: "/film/share.jpg", width: 1200, height: 675, alt: "Ophi: one assistant, one memory" }] },
  twitter: { card: "summary_large_image", title, description, images: ["/film/share.jpg"] },
};

// Optional fields take the clinic-software control's outline; typed text stays 16px on phones so iOS doesn't zoom.
const field = "h-[46px] w-full min-w-0 rounded-full border border-band-line bg-transparent px-5 text-[13px] text-ink outline-none transition-[border-color,background] duration-250 placeholder:text-muted placeholder:opacity-100 hover:border-field-line hover:bg-field focus:border-sage-deep focus:bg-field phone:text-[16px] phone:placeholder:text-[13px]";

export default function FilmPage() {
  return (
    <div className="mx-auto flex min-h-svh w-[min(calc(100%-112px),1180px)] flex-col tablet:w-[calc(100%-72px)] phone:w-[calc(100%-40px)] small:w-[calc(100%-32px)]">
      <header className="flex h-[98px] flex-none items-center phone:h-[84px]">
        <Link className="inline-block pr-[7px] text-[46px] leading-none font-[650] tracking-[-3.7px] phone:text-[38px] phone:tracking-[-3px]" href="/" aria-label="Ophi home">ophi<span className="text-rust" aria-hidden="true">.</span></Link>
      </header>
      <main className="flex-1">
        <section aria-labelledby="film-title">
          <h1 id="film-title" className="text-[length:clamp(40px,5.4vw,76px)] leading-[1.02] tracking-[-.05em] motion-safe:animate-[arrive_.75s_ease-out_both]">One assistant, <em>for every patient.</em></h1>
          <p className="mt-4 text-[17px] leading-[1.6] text-[#55624e] phone:text-[16px] phone:text-pretty">A 90-second look at what we’re building for dental clinics.</p>
          <FilmPlayer src="/film/ophi-demo.mp4" poster="/film/poster.jpg" length="1:30" />
        </section>
        {/* The film ends on "leave your email, or call us": both are here, in the homepage's signup band. */}
        <div className="my-9 grid grid-cols-[minmax(0,1fr)_minmax(0,490px)] gap-x-[6%] rounded-[36px] bg-sage p-11 tablet:grid-cols-[minmax(0,1fr)_minmax(0,440px)] phone:flex phone:flex-col phone:gap-7 phone:rounded-[28px] phone:px-5 phone:pt-[26px] phone:pb-6">
          <div className="flex flex-col items-start gap-4.5">
            <h2 className="text-[28px] leading-[1.15] tracking-[-.7px] phone:text-[25px] small:text-[23px]">Want Ophi at your clinic?</h2>
            <p className="max-w-[400px] text-[15px] leading-[1.6] text-[#55624e] phone:text-pretty">Leave your email and we’ll write when Ophi is ready for you. Add a number if you’d rather talk.</p>
            <a className={pill({ surface: "band", className: "mt-1" })} href={PHONE.href}>Or call us at {PHONE.shown}<span className={pillTag({ surface: "band" })}><Icon name="arrow" className={`${pillIcon} group-hover/pill:translate-x-px group-hover/pill:-translate-y-px`} /></span></a>
          </div>
          <section aria-label="Leave your details">
            <WaitlistForm action={leaveDetails}>
              <div className="mt-2.5 grid grid-cols-2 gap-2.5 narrow:grid-cols-1">
                <label className="sr-only" htmlFor="name">Your name (optional)</label>
                <input id="name" name="name" type="text" autoComplete="name" maxLength={120} placeholder="Your name (optional)" className={field} />
                <label className="sr-only" htmlFor="phone">Phone number (optional)</label>
                <input id="phone" name="phone" type="tel" autoComplete="tel" inputMode="tel" maxLength={40} placeholder="Phone (optional)" className={field} />
              </div>
            </WaitlistForm>
          </section>
        </div>
      </main>
      <footer className="mt-auto flex min-h-[62px] items-center justify-between gap-6 border-t border-line text-[11px] text-muted [box-shadow:var(--crease)] phone:py-4">
        <span>© {new Date().getFullYear()} Ophi</span>
        <InfoPanel kind="privacy" note="If you add your name or phone number, they reach us by email, and we use them only to contact you about Ophi." />
      </footer>
    </div>
  );
}
