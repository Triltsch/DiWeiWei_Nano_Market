/**
 * Terms of Service Page
 *
 * Displays the terms and conditions for using DiWeiWei Nano Market.
 * This is a placeholder page that should be updated with actual legal content.
 */

import { useLanguage } from "../../../shared/i18n";

interface TermsSection {
  heading: string;
  body: string;
}

interface TermsContent {
  title: string;
  sections: TermsSection[];
  lastUpdated: string;
}

const TERMS_CONTENT: Record<"de" | "en", TermsContent> = {
  de: {
    title: "Nutzungsbedingungen",
    sections: [
      {
        heading: "1. Zustimmung zu den Bedingungen",
        body: "Durch den Zugriff auf und die Nutzung des DiWeiWei Nano Market (\"die Plattform\") akzeptieren Sie diese Nutzungsbedingungen. Wenn Sie nicht zustimmen, nutzen Sie die Plattform bitte nicht.",
      },
      {
        heading: "2. Leistungsbeschreibung",
        body: "DiWeiWei Nano Market bietet eine Plattform zum Teilen und Entdecken von Nano-Inhalten (kurzformatige Lern- und Kreativinhalte). Der Service umfasst Funktionen für Inhaltserstellung, Upload, Suche und Community-Interaktion.",
      },
      {
        heading: "3. Benutzerkonten",
        body: "Sie sind für die Vertraulichkeit Ihrer Zugangsdaten und alle Aktivitäten unter Ihrem Konto verantwortlich. Sie verpflichten sich, uns über jede unbefugte Nutzung Ihres Kontos unverzüglich zu informieren.",
      },
      {
        heading: "4. Inhaltsrichtlinien",
        body: "Nutzende sind für hochgeladene Inhalte verantwortlich. Inhalte dürfen keine geistigen Eigentumsrechte verletzen, kein schädliches oder rechtswidriges Material enthalten und keine geltenden Gesetze verletzen.",
      },
      {
        heading: "5. Geistiges Eigentum",
        body: "Hochgeladene Inhalte bleiben geistiges Eigentum der Erstellerinnen und Ersteller. Durch den Upload gewähren Sie der Plattform eine Lizenz zur Anzeige, Verbreitung und Bewerbung Ihrer Inhalte innerhalb des Dienstes.",
      },
      {
        heading: "6. Datenschutz",
        body: "Die Nutzung der Plattform unterliegt auch unserer Datenschutzerklärung. Bitte lesen Sie diese, um unsere Verfahren zur Erhebung und Verwendung personenbezogener Daten zu verstehen.",
      },
      {
        heading: "7. Beendigung",
        body: "Wir behalten uns das Recht vor, den Zugang zur Plattform jederzeit und ohne Vorankündigung zu beenden oder auszusetzen, insbesondere bei Verstößen gegen diese Nutzungsbedingungen.",
      },
      {
        heading: "8. Änderungen der Bedingungen",
        body: "Wir können diese Nutzungsbedingungen jederzeit ändern. Über wesentliche Änderungen informieren wir per E-Mail oder Plattformhinweis. Die fortgesetzte Nutzung gilt als Zustimmung zu den geänderten Bedingungen.",
      },
      {
        heading: "9. Kontakt",
        body: "Wenn Sie Fragen zu diesen Nutzungsbedingungen haben, kontaktieren Sie uns bitte über die Support-Kanäle der Plattform.",
      },
    ],
    lastUpdated: "Zuletzt aktualisiert: 9. März 2026",
  },
  en: {
    title: "Terms of Service",
    sections: [
      {
        heading: "1. Acceptance of Terms",
        body: "By accessing and using DiWeiWei Nano Market (\"the Platform\"), you accept and agree to be bound by the terms and provisions of this agreement. If you do not agree to these Terms of Service, please do not use the Platform.",
      },
      {
        heading: "2. Description of Service",
        body: "DiWeiWei Nano Market provides a platform for sharing and discovering nano-content (short-form educational and creative content). The service includes features for content creation, uploading, searching, and community interaction.",
      },
      {
        heading: "3. User Accounts",
        body: "You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account.",
      },
      {
        heading: "4. Content Guidelines",
        body: "Users are responsible for the content they upload to the Platform. Content must not violate intellectual property rights, contain harmful or illegal material, or violate applicable laws and regulations.",
      },
      {
        heading: "5. Intellectual Property",
        body: "Content uploaded to the Platform remains the intellectual property of the creator. By uploading content, you grant the Platform a license to display, distribute, and promote your content within the service.",
      },
      {
        heading: "6. Privacy",
        body: "Your use of the Platform is also governed by our Privacy Policy. Please review our Privacy Policy to understand our practices regarding the collection and use of your personal information.",
      },
      {
        heading: "7. Termination",
        body: "We reserve the right to terminate or suspend access to the Platform immediately, without prior notice, for any reason whatsoever, including breach of these Terms of Service.",
      },
      {
        heading: "8. Changes to Terms",
        body: "We reserve the right to modify these Terms of Service at any time. We will notify users of material changes via email or platform notification. Continued use of the Platform after changes constitutes acceptance of the modified terms.",
      },
      {
        heading: "9. Contact",
        body: "If you have questions about these Terms of Service, please contact us through the Platform support channels.",
      },
    ],
    lastUpdated: "Last updated: March 9, 2026",
  },
};

export function TermsPage(): JSX.Element {
  const { language } = useLanguage();
  const content = TERMS_CONTENT[language];

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="card-elevated p-8">
        <h1 className="text-3xl font-bold text-primary-700 mb-6">{content.title}</h1>

        <div className="prose prose-neutral max-w-none space-y-6 text-neutral-700">
          {content.sections.map((section) => (
            <section key={section.heading}>
              <h2 className="text-2xl font-semibold text-neutral-900 mb-3">{section.heading}</h2>
              <p>{section.body}</p>
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
