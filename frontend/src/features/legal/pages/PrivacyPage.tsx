/**
 * Privacy Policy Page
 *
 * Displays the privacy policy for DiWeiWei Nano Market.
 * This is a placeholder page that should be updated with actual legal content
 * and compliance requirements (GDPR, CCPA, etc.).
 */

export function PrivacyPage(): JSX.Element {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="card-elevated p-8">
        <h1 className="text-3xl font-bold text-primary-700 mb-6">Privacy Policy</h1>
        
        <div className="prose prose-neutral max-w-none space-y-6 text-neutral-700">
          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">1. Information We Collect</h2>
            <p>
              We collect information you provide directly to us when you create an account, upload content,
              or interact with the Platform. This includes:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Account information (email, username, password)</li>
              <li>Profile information (optional bio, avatar)</li>
              <li>Content you upload (nanos, descriptions, metadata)</li>
              <li>Usage data (interactions, searches, preferences)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">2. How We Use Your Information</h2>
            <p>
              We use the information we collect to:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide, maintain, and improve the Platform</li>
              <li>Personalize your experience and content recommendations</li>
              <li>Communicate with you about updates, security alerts, or support</li>
              <li>Monitor and analyze usage patterns to improve our services</li>
              <li>Detect, prevent, and address security or technical issues</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">3. Data Sharing and Disclosure</h2>
            <p>
              We do not sell your personal information. We may share your information only in the
              following circumstances:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>With your consent</li>
              <li>To comply with legal obligations</li>
              <li>To protect our rights and prevent fraud or security issues</li>
              <li>With service providers who assist in operating the Platform</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">4. Your Rights (GDPR Compliance)</h2>
            <p>
              Under GDPR and other privacy regulations, you have the right to:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Request correction of inaccurate data</li>
              <li><strong>Erasure:</strong> Request deletion of your personal data ("right to be forgotten")</li>
              <li><strong>Data Portability:</strong> Request transfer of your data in a machine-readable format</li>
              <li><strong>Restriction:</strong> Request limitation of processing in certain situations</li>
              <li><strong>Object:</strong> Object to processing based on legitimate interests</li>
            </ul>
            <p className="mt-3">
              To exercise these rights, please use the account settings page or contact our support team.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">5. Data Retention</h2>
            <p>
              We retain your personal information for as long as necessary to provide our services and
              fulfill the purposes outlined in this Privacy Policy. When you delete your account, we will
              delete or anonymize your personal data, except where retention is required by law.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">6. Security</h2>
            <p>
              We implement appropriate technical and organizational measures to protect your personal
              information against unauthorized access, alteration, disclosure, or destruction. This includes
              encryption, secure password hashing, and regular security audits.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">7. Cookies and Tracking</h2>
            <p>
              We use cookies and similar tracking technologies to improve your experience, analyze usage
              patterns, and provide personalized content. You can control cookie preferences through your
              browser settings.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">8. Children's Privacy</h2>
            <p>
              The Platform is not intended for users under the age of 16. We do not knowingly collect
              personal information from children under 16. If we become aware of such collection, we will
              take steps to delete the information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">9. International Data Transfers</h2>
            <p>
              Your information may be transferred to and processed in countries other than your country of
              residence. We ensure appropriate safeguards are in place to protect your data in accordance
              with this Privacy Policy.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">10. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of material changes
              by email or through a notice on the Platform. Your continued use after changes constitutes
              acceptance of the updated policy.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">11. Contact Us</h2>
            <p>
              If you have questions about this Privacy Policy or wish to exercise your privacy rights,
              please contact us through the Platform support channels or at the email address provided
              in your account settings.
            </p>
          </section>

          <p className="text-sm text-neutral-500 mt-8 pt-4 border-t border-neutral-200">
            Last updated: March 9, 2026
          </p>
        </div>
      </div>
    </div>
  );
}
