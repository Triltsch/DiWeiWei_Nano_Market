import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useTranslation } from "../../../shared/i18n";
import { useAuth } from "../AuthContext";

interface LoginFormValues {
  email: string;
  password: string;
  rememberMe: boolean;
}

const REMEMBERED_EMAIL_KEY = "auth_remembered_email";

export function LoginPage(): JSX.Element {
  const { t } = useTranslation();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  const rememberedEmail = useMemo(() => localStorage.getItem(REMEMBERED_EMAIL_KEY) ?? "", []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isValid },
  } = useForm<LoginFormValues>({
    mode: "onChange",
    defaultValues: {
      email: rememberedEmail,
      password: "",
      rememberMe: Boolean(rememberedEmail),
    },
  });

  /**
   * Validates redirect target to prevent open redirect attacks.
   * - Must start with `/` (local path)
   * - Cannot start with `//` (protocol-relative URL)
   */
  function isValidRedirect(url: string): boolean {
    return url.startsWith("/") && !url.startsWith("//");
  }

  const rawRedirect = searchParams.get("redirect") ?? "/dashboard";
  const redirectTarget = isValidRedirect(rawRedirect) ? rawRedirect : "/dashboard";

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);

    try {
      await login(values.email, values.password);

      if (values.rememberMe) {
        localStorage.setItem(REMEMBERED_EMAIL_KEY, values.email);
      } else {
        localStorage.removeItem(REMEMBERED_EMAIL_KEY);
      }

      navigate(redirectTarget);
    } catch (error) {
      const message = error instanceof Error ? error.message : t("login_error_default");
      setFormError(message);
    }
  });

  return (
    <section className="card-elevated max-w-xl mx-auto space-y-4">
      <h1 className="text-primary-600">{t("login_title")}</h1>
      <p className="text-neutral-600">{t("login_subtitle")}</p>

      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-1">
          <label htmlFor="login-email" className="font-medium text-neutral-700">
            {t("login_email_label")}
          </label>
          <input
            id="login-email"
            type="email"
            className="w-full border border-neutral-300 rounded-lg px-3 py-2"
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? "login-email-error" : undefined}
            {...register("email", {
              required: t("login_email_required"),
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: t("login_email_invalid"),
              },
            })}
          />
          {errors.email && (
            <p id="login-email-error" className="text-sm text-red-600">
              {errors.email.message}
            </p>
          )}
        </div>

        <div className="space-y-1">
          <label htmlFor="login-password" className="font-medium text-neutral-700">
            {t("login_password_label")}
          </label>
          <div className="flex gap-2">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              className="w-full border border-neutral-300 rounded-lg px-3 py-2"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? "login-password-error" : undefined}
              {...register("password", {
                required: t("login_password_required"),
              })}
            />
            <button
              type="button"
              className="btn-outline"
              onClick={() => setShowPassword((previous) => !previous)}
            >
              {showPassword ? t("auth_hide_password") : t("auth_show_password")}
            </button>
          </div>
          {errors.password && (
            <p id="login-password-error" className="text-sm text-red-600">
              {errors.password.message}
            </p>
          )}
        </div>

        <label className="flex items-center gap-2 text-sm text-neutral-700">
          <input type="checkbox" {...register("rememberMe")} />
          {t("login_remember_email")}
        </label>

        {formError && (
          <p className="text-sm text-red-600" role="alert">
            {formError}
          </p>
        )}

        <button type="submit" className="btn-primary w-full" disabled={!isValid || isSubmitting}>
          {isSubmitting ? t("login_submitting") : t("login_submit")}
        </button>
      </form>

      <div className="text-sm text-neutral-700 space-y-2">
        <p>
          <a href="/faq" className="underline">
            {t("login_forgot_password")}
          </a>
        </p>
        <p>
          {t("login_no_account")} <Link to="/register">{t("login_create_account_link")}</Link>
        </p>
      </div>
    </section>
  );
}
