import SiteLogo from "./SiteLogo"
import { CONTACT_DETAILS, FOOTER_LINKS, WHATSAPP_URL } from "../content/siteContent"

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <div className="site-footer-brand">
          <a href="/" className="site-footer-logo-link">
            <SiteLogo compact />
          </a>
          <p>
            AI-powered digital health audits for businesses across the world. Review your Google presence,
            website quality, social visibility, and competitive gaps from one place.
          </p>
        </div>

        <div className="site-footer-links">
          <div className="site-footer-column">
            <h4>Company</h4>
            <a href="/about-us">About Us</a>
            <a href="/contact-us">Contact Us</a>
            <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">WhatsApp</a>
          </div>

          <div className="site-footer-column">
            <h4>Contact</h4>
            {CONTACT_DETAILS.addressLines.map((line) => (
              <p key={line}>{line}</p>
            ))}
            <a href={`tel:${CONTACT_DETAILS.phoneHref}`}>{CONTACT_DETAILS.phoneDisplay}</a>
          </div>
        </div>
      </div>

      <div className="site-footer-bottom">
        <span>© {new Date().getFullYear()} Aidbro. All rights reserved.</span>
        <div className="site-footer-bottom-links">
          {FOOTER_LINKS.map((link) => (
            <a key={link.href} href={link.href}>{link.label}</a>
          ))}
        </div>
      </div>
    </footer>
  )
}
