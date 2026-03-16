/**
 * Privacy Policy Page
 *
 * Displays the privacy policy for DiWeiWei Nano Market.
 * This is a placeholder page that should be updated with actual legal content
 * and compliance requirements (GDPR, CCPA, etc.).
 */

import { useLanguage } from "../../../shared/i18n";

interface PrivacySection {
  heading: string;
  body: string;
  bullets?: string[];
  note?: string;
}

interface PrivacyContent {
  title: string;
  sections: PrivacySection[];
  lastUpdated: string;
}

const PRIVACY_CONTENT: Record<"de" | "en", PrivacyContent> = {
  de: {
    title: "Datenschutzerklärung",
    sections: [
      {
        heading: "1. Welche Informationen wir erfassen",
        body: "Wir erfassen Informationen, die Sie uns direkt bereitstellen, wenn Sie ein Konto erstellen, Inhalte hochladen oder mit der Plattform interagieren. Dazu gehören:",
        bullets: [
          "Kontoinformationen (E-Mail, Benutzername, Passwort)",
          "Profilinformationen (optionale Bio, Avatar)",
          "Von Ihnen hochgeladene Inhalte (Nanos, Beschreibungen, Metadaten)",
          "Nutzungsdaten (Interaktionen, Suchen, Präferenzen)",
        ],
      },
      {
        heading: "2. Wie wir Ihre Informationen verwenden",
        body: "Wir verwenden die erfassten Informationen, um:",
        bullets: [
          "die Plattform bereitzustellen, zu betreiben und zu verbessern",
          "Ihr Nutzungserlebnis und Inhaltsempfehlungen zu personalisieren",
          "Sie über Updates, Sicherheitsmeldungen oder Support zu informieren",
          "Nutzungsmuster zu analysieren und unsere Services zu optimieren",
          "Sicherheits- und technische Probleme zu erkennen, zu verhindern und zu beheben",
        ],
      },
      {
        heading: "3. Datenweitergabe und Offenlegung",
        body: "Wir verkaufen keine personenbezogenen Daten. Wir teilen Daten nur in folgenden Fällen:",
        bullets: [
          "mit Ihrer Einwilligung",
          "zur Erfüllung rechtlicher Verpflichtungen",
          "zum Schutz unserer Rechte sowie zur Betrugs- und Sicherheitsprävention",
          "mit Dienstleistern, die uns beim Betrieb der Plattform unterstützen",
        ],
      },
      {
        heading: "4. Ihre Rechte (DSGVO)",
        body: "Nach DSGVO und anderen Datenschutzregelungen haben Sie das Recht auf:",
        bullets: [
          "Auskunft: Kopie Ihrer personenbezogenen Daten anfordern",
          "Berichtigung: Korrektur unrichtiger Daten verlangen",
          "Löschung: Löschung Ihrer Daten verlangen (\"Recht auf Vergessenwerden\")",
          "Datenübertragbarkeit: Übermittlung in maschinenlesbarem Format verlangen",
          "Einschränkung: Verarbeitung in bestimmten Fällen einschränken",
          "Widerspruch: Verarbeitung auf Basis berechtigter Interessen widersprechen",
        ],
        note: "Zur Ausübung Ihrer Rechte nutzen Sie bitte die Kontoeinstellungen oder kontaktieren Sie den Support.",
      },
      {
        heading: "5. Datenaufbewahrung",
        body: "Wir speichern personenbezogene Daten nur so lange, wie es für die Bereitstellung der Services und die in dieser Erklärung genannten Zwecke erforderlich ist. Bei Löschung des Kontos löschen oder anonymisieren wir die Daten, sofern keine gesetzliche Aufbewahrungspflicht besteht.",
      },
      {
        heading: "6. Sicherheit",
        body: "Wir setzen geeignete technische und organisatorische Maßnahmen zum Schutz personenbezogener Daten gegen unbefugten Zugriff, Veränderung, Offenlegung oder Zerstörung ein. Dazu gehören Verschlüsselung, sicheres Passwort-Hashing und regelmäßige Sicherheitsprüfungen.",
      },
      {
        heading: "7. Cookies und Tracking",
        body: "Wir verwenden Cookies und ähnliche Technologien, um Ihr Nutzungserlebnis zu verbessern, Nutzungsverhalten zu analysieren und personalisierte Inhalte bereitzustellen. Cookie-Einstellungen können Sie in Ihrem Browser verwalten.",
      },
      {
        heading: "8. Datenschutz von Kindern",
        body: "Die Plattform richtet sich nicht an Personen unter 16 Jahren. Wir erfassen wissentlich keine personenbezogenen Daten von Kindern unter 16 Jahren. Werden uns solche Daten bekannt, löschen wir sie unverzüglich.",
      },
      {
        heading: "9. Internationale Datenübermittlungen",
        body: "Ihre Daten können in andere Länder übertragen und dort verarbeitet werden. Wir stellen sicher, dass angemessene Schutzmaßnahmen gemäß dieser Datenschutzerklärung bestehen.",
      },
      {
        heading: "10. Änderungen dieser Richtlinie",
        body: "Wir können diese Datenschutzerklärung von Zeit zu Zeit aktualisieren. Über wesentliche Änderungen informieren wir per E-Mail oder Plattformhinweis. Die weitere Nutzung gilt als Zustimmung zur aktualisierten Richtlinie.",
      },
      {
        heading: "11. Kontakt",
        body: "Bei Fragen zur Datenschutzerklärung oder zur Ausübung Ihrer Rechte kontaktieren Sie uns bitte über die Support-Kanäle der Plattform oder die in den Kontoeinstellungen angegebene E-Mail-Adresse.",
      },
    ],
    lastUpdated: "Zuletzt aktualisiert: 9. März 2026",
  },
  en: {
    title: "Privacy Policy",
    sections: [
      {
        heading: "1. Information We Collect",
        body: "We collect information you provide directly to us when you create an account, upload content, or interact with the Platform. This includes:",
        bullets: [
          "Account information (email, username, password)",
          "Profile information (optional bio, avatar)",
          "Content you upload (nanos, descriptions, metadata)",
          "Usage data (interactions, searches, preferences)",
        ],
      },
      {
        heading: "2. How We Use Your Information",
        body: "We use the information we collect to:",
        bullets: [
          "Provide, maintain, and improve the Platform",
          "Personalize your experience and content recommendations",
          "Communicate with you about updates, security alerts, or support",
          "Monitor and analyze usage patterns to improve our services",
          "Detect, prevent, and address security or technical issues",
        ],
      },
      {
        heading: "3. Data Sharing and Disclosure",
        body: "We do not sell your personal information. We may share your information only in the following circumstances:",
        bullets: [
          "With your consent",
          "To comply with legal obligations",
          "To protect our rights and prevent fraud or security issues",
          "With service providers who assist in operating the Platform",
        ],
      },
      {
        heading: "4. Your Rights (GDPR Compliance)",
        body: "Under GDPR and other privacy regulations, you have the right to:",
        bullets: [
          "Access: Request a copy of your personal data",
          "Rectification: Request correction of inaccurate data",
          "Erasure: Request deletion of your personal data (\"right to be forgotten\")",
          "Data Portability: Request transfer of your data in a machine-readable format",
          "Restriction: Request limitation of processing in certain situations",
          "Object: Object to processing based on legitimate interests",
        ],
        note: "To exercise these rights, please use the account settings page or contact our support team.",
      },
      {
        heading: "5. Data Retention",
        body: "We retain your personal information for as long as necessary to provide our services and fulfill the purposes outlined in this Privacy Policy. When you delete your account, we will delete or anonymize your personal data, except where retention is required by law.",
      },
      {
        heading: "6. Security",
        body: "We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. This includes encryption, secure password hashing, and regular security audits.",
      },
      {
        heading: "7. Cookies and Tracking",
        body: "We use cookies and similar tracking technologies to improve your experience, analyze usage patterns, and provide personalized content. You can control cookie preferences through your browser settings.",
      },
      {
        heading: "8. Children's Privacy",
        body: "The Platform is not intended for users under the age of 16. We do not knowingly collect personal information from children under 16. If we become aware of such collection, we will take steps to delete the information.",
      },
      {
        heading: "9. International Data Transfers",
        body: "Your information may be transferred to and processed in countries other than your country of residence. We ensure appropriate safeguards are in place to protect your data in accordance with this Privacy Policy.",
      },
      {
        heading: "10. Changes to This Policy",
        body: "We may update this Privacy Policy from time to time. We will notify you of material changes by email or through a notice on the Platform. Your continued use after changes constitutes acceptance of the updated policy.",
      },
      {
        heading: "11. Contact Us",
        body: "If you have questions about this Privacy Policy or wish to exercise your privacy rights, please contact us through the Platform support channels or at the email address provided in your account settings.",
      },
    ],
    lastUpdated: "Last updated: March 9, 2026",
  },
};

export function PrivacyPage(): JSX.Element {
  const { language } = useLanguage();
  const content = PRIVACY_CONTENT[language];

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="card-elevated p-8">
        <h1 className="text-3xl font-bold text-primary-700 mb-6">{content.title}</h1>

        <div className="prose prose-neutral max-w-none space-y-6 text-neutral-700">
          {content.sections.map((section) => (
            <section key={section.heading}>
              <h2 className="text-2xl font-semibold text-neutral-900 mb-3">{section.heading}</h2>
              <p>{section.body}</p>
              {section.bullets && (
                <ul className="list-disc pl-6 space-y-2">
                  {section.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              )}
              {section.note && <p className="mt-3">{section.note}</p>}
            </section>
          ))}

          <p className="text-sm text-neutral-500 mt-8 pt-4 border-t border-neutral-200">
            {content.lastUpdated}
          </p>
        </div>
      </div>
    </div>
  );
}
