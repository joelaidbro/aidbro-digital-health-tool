import SiteLogo from "../components/SiteLogo"
import SiteFooter from "../components/SiteFooter"
import { CONTACT_DETAILS } from "../content/siteContent"

export default function InfoPage({ page }) {
  if (!page) {
    return null
  }

  return (
    <div className="info-page">
      <div className="info-page-topbar">
        <a href="/" className="navbar-logo">
          <SiteLogo badge="Digital Health Tool" />
        </a>
        <div className="navbar-links info-page-links">
          <a href="/about-us">About Us</a>
          <a href="/privacy-policy">Privacy Policy</a>
          <a href="/contact-us">Contact Us</a>
        </div>
      </div>

      <main className="info-page-content">
        <section className="info-page-hero fade-up">
          <div className="hero-badge">
            <span className="dot" />
            Aidbro Information Centre
          </div>
          <h1>{page.title}</h1>
          <p>{page.subtitle}</p>
        </section>

        <section className="info-page-card fade-up-d1">
          {page.sections.map((section) => (
            <div key={section.heading} className="info-section">
              <h2>{section.heading}</h2>
              {section.paragraphs?.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
              {section.list?.length ? (
                <ul className="info-list">
                  {section.list.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}

          <div className="info-contact-block">
            <h3>Registered Contact</h3>
            <p>{CONTACT_DETAILS.company}</p>
            {CONTACT_DETAILS.addressLines.map((line) => (
              <p key={line}>{line}</p>
            ))}
            <p>Mobile No: {CONTACT_DETAILS.phoneDisplay}</p>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
