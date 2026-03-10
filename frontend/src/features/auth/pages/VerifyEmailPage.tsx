import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { resendVerificationEmail, verifyEmail } from "../api";

export function VerifyEmailPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const verificationToken = searchParams.get("token");
  const email = searchParams.get("email") ?? "";

  useEffect(() => {
    if (!verificationToken) {
      return;
    }

    let active = true;
    let timeoutId: NodeJS.Timeout | null = null;

    const verify = async (): Promise<void> => {
      setIsSubmitting(true);
      setStatusMessage(null);
      setErrorMessage(null);

      try {
        await verifyEmail(verificationToken);

        if (!active) {
          return;
        }

        setStatusMessage("Email verified! Redirecting to login...");
        timeoutId = setTimeout(() => {
          if (active) {
            navigate("/login");
          }
        }, 2000);
      } catch {
        if (!active) {
          return;
        }
        setErrorMessage("Link expired or invalid. Request new email.");
      } finally {
        if (active) {
          setIsSubmitting(false);
        }
      }
    };

    void verify();

    return () => {
      active = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [verificationToken, navigate]);

  useEffect(() => {
    if (cooldownSeconds <= 0) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setCooldownSeconds((seconds) => Math.max(0, seconds - 1));
    }, 1000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [cooldownSeconds]);

  const canResend = useMemo(
    () => email.length > 0 && cooldownSeconds === 0 && !isSubmitting,
    [email, cooldownSeconds, isSubmitting]
  );

  const handleResend = async (): Promise<void> => {
    if (!email || !canResend) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await resendVerificationEmail(email);
      setStatusMessage(response.message || "Verification email resent.");
      setCooldownSeconds(30);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to resend verification email.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="card-elevated max-w-xl mx-auto space-y-4">
      <h1 className="text-primary-600">Verify Email</h1>
      <p className="text-neutral-700">Check your email for verification link.</p>
      <p className="text-sm text-neutral-600">Registered email: {email || "(not provided)"}</p>

      {statusMessage && <p className="text-sm text-green-700">{statusMessage}</p>}
      {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}

      <button
        type="button"
        className="btn-primary w-full"
        onClick={() => {
          void handleResend();
        }}
        disabled={!canResend}
      >
        {cooldownSeconds > 0
          ? `Resend verification email (${cooldownSeconds}s)`
          : "Resend verification email"}
      </button>

      {!email && (
        <p className="text-sm text-neutral-600">
          Register again to provide an email for resending verification links.
        </p>
      )}

      <p className="text-sm text-neutral-700">
        Already verified? <Link to="/login">Go to login</Link>
      </p>
    </section>
  );
}
