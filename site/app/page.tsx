import { WaitlistForm } from "@/components/waitlist-form";
import { ToothScene } from "@/components/tooth-scene";
import { InfoPanel } from "@/components/info-panel";
import Link from "next/link";
import { Icon } from "@/components/icons";
import { CopyEmail } from "@/components/copy-email";
import { copy } from "@/lib/copy";

export default function Page() {
  return (
    <div className="site-shell" id="top">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="site-header">
        <Link className="wordmark" href="/" aria-label="Ophi home">ophi<span aria-hidden="true">.</span></Link>
        <span className="launch-status"><span aria-hidden="true" />In the making</span>
      </header>
      <main id="main">
        <section className="poster" aria-labelledby="poster-title">
          <h1 id="poster-title" className="poster-title"><span>Good care.</span><em>Less paperwork.</em></h1>
          <div className="sculpture">
            <div className="orbit" aria-hidden="true" />
            <ToothScene />
          </div>
        </section>
        <div className="entry-row">
          <div className="introduction">
            <p>We’re building for dental teams who’d rather spend their time on people.</p>
            <div className="introduction-actions"><InfoPanel kind="why" /></div>
          </div>
          <section id="join" className="signup" aria-labelledby="signup-title">
            <div className="signup-head">
              <h2 id="signup-title">Be here from the beginning.</h2>
              <p className="signup-note">Get occasional updates and hear when Ophi is ready.</p>
            </div>
            <WaitlistForm />
          </section>
        </div>
        <section className="faq" aria-labelledby="faq-title">
          <div className="faq-head">
            <h2 id="faq-title">A few quick answers.</h2>
            {/* Contact lives with the questions, keeping the signup band to one action. */}
            <div className="contact">
              <p>Anything else? Write to us.</p>
              <CopyEmail email={copy.contactEmail} />
            </div>
          </div>
          <div className="faq-items">
            <details>
              <summary>Who is Ophi for?<Icon name="plus" /></summary>
              <p>Dental teams handling treatment paperwork and preauthorization requests.</p>
            </details>
            <details>
              <summary>What are you building?<Icon name="plus" /></summary>
              <p>Tools that help dental teams prepare preauthorization requests, so less time goes to paperwork.</p>
            </details>
            <details>
              <summary>When can I try it?<Icon name="plus" /></summary>
              <p>We’re still building. Join the waitlist to hear when Ophi is ready.</p>
            </details>
          </div>
        </section>
      </main>
      <footer className="site-footer">
        <div className="footer-wordmark" aria-hidden="true"><span>ophi</span><span className="footer-flower">✳</span></div>
        <div className="footer-bottom"><span>© {new Date().getFullYear()} Ophi</span><div className="footer-actions"><InfoPanel kind="privacy" /><a className="pill back-to-top" href="#top">Back to the top<span className="pill-tag"><Icon name="up" /></span></a></div></div>
      </footer>
    </div>
  );
}
