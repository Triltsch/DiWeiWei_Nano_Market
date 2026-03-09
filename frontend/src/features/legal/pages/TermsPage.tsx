/**
 * Terms of Service Page
 *
 * Displays the terms and conditions for using DiWeiWei Nano Market.
 * This is a placeholder page that should be updated with actual legal content.
 */

export function TermsPage(): JSX.Element {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="card-elevated p-8">
        <h1 className="text-3xl font-bold text-primary-700 mb-6">Terms of Service</h1>
        
        <div className="prose prose-neutral max-w-none space-y-6 text-neutral-700">
          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing and using DiWeiWei Nano Market ("the Platform"), you accept and agree to be bound by
              the terms and provisions of this agreement. If you do not agree to these Terms of Service,
              please do not use the Platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">2. Description of Service</h2>
            <p>
              DiWeiWei Nano Market provides a platform for sharing and discovering nano-content (short-form
              educational and creative content). The service includes features for content creation, uploading,
              searching, and community interaction.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">3. User Accounts</h2>
            <p>
              You are responsible for maintaining the confidentiality of your account credentials and for all
              activities that occur under your account. You agree to notify us immediately of any unauthorized
              use of your account.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">4. Content Guidelines</h2>
            <p>
              Users are responsible for the content they upload to the Platform. Content must not violate
              intellectual property rights, contain harmful or illegal material, or violate applicable laws
              and regulations.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">5. Intellectual Property</h2>
            <p>
              Content uploaded to the Platform remains the intellectual property of the creator. By uploading
              content, you grant the Platform a license to display, distribute, and promote your content
              within the service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">6. Privacy</h2>
            <p>
              Your use of the Platform is also governed by our Privacy Policy. Please review our Privacy
              Policy to understand our practices regarding the collection and use of your personal information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">7. Termination</h2>
            <p>
              We reserve the right to terminate or suspend access to the Platform immediately, without prior
              notice, for any reason whatsoever, including breach of these Terms of Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">8. Changes to Terms</h2>
            <p>
              We reserve the right to modify these Terms of Service at any time. We will notify users of
              material changes via email or platform notification. Continued use of the Platform after
              changes constitutes acceptance of the modified terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-3">9. Contact</h2>
            <p>
              If you have questions about these Terms of Service, please contact us through the Platform
              support channels.
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
