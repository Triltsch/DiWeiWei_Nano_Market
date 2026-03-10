import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { registerUser } from "../api";
import {
  getPasswordStrength,
  meetsPasswordPolicy,
  PASSWORD_REQUIREMENTS,
} from "../passwordStrength";

interface RegisterFormValues {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
}

export function RegisterPage(): JSX.Element {
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting, isValid },
  } = useForm<RegisterFormValues>({
    mode: "onChange",
    defaultValues: {
      email: "",
      username: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false,
      acceptPrivacy: false,
    },
  });

  const password = watch("password");
  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);

    try {
      await registerUser({
        email: values.email,
        username: values.username,
        password: values.password,
        acceptTerms: values.acceptTerms,
        acceptPrivacy: values.acceptPrivacy,
      });

      navigate(`/verify-email?email=${encodeURIComponent(values.email)}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Registration failed.";
      setFormError(message);
    }
  });

  return (
    <section className="card-elevated max-w-xl mx-auto space-y-4">
      <h1 className="text-primary-600">Register</h1>
      <p className="text-neutral-600">Create your account to start using DiWeiWei Nano Market.</p>

      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-1">
          <label htmlFor="register-email" className="font-medium text-neutral-700">
            Email
          </label>
          <input
            id="register-email"
            type="email"
            className="w-full border border-neutral-300 rounded-lg px-3 py-2"
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? "register-email-error" : undefined}
            {...register("email", {
              required: "Email is required",
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: "Please enter a valid email address",
              },
            })}
          />
          {errors.email && (
            <p id="register-email-error" className="text-sm text-red-600">
              {errors.email.message}
            </p>
          )}
        </div>

        <div className="space-y-1">
          <label htmlFor="register-username" className="font-medium text-neutral-700">
            Username
          </label>
          <input
            id="register-username"
            type="text"
            className="w-full border border-neutral-300 rounded-lg px-3 py-2"
            aria-invalid={Boolean(errors.username)}
            aria-describedby={errors.username ? "register-username-error" : undefined}
            {...register("username", {
              required: "Username is required",
              minLength: { value: 3, message: "Username must be at least 3 characters" },
              maxLength: { value: 20, message: "Username must be at most 20 characters" },
              pattern: {
                value: /^[a-zA-Z0-9_]+$/,
                message: "Only letters, numbers, and underscore are allowed",
              },
            })}
          />
          {errors.username && (
            <p id="register-username-error" className="text-sm text-red-600">
              {errors.username.message}
            </p>
          )}
        </div>

        <div className="space-y-1">
          <label htmlFor="register-password" className="font-medium text-neutral-700">
            Password
          </label>
          <div className="flex gap-2">
            <input
              id="register-password"
              type={showPassword ? "text" : "password"}
              className="w-full border border-neutral-300 rounded-lg px-3 py-2"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? "register-password-error" : undefined}
              {...register("password", {
                required: "Password is required",
                validate: (value) =>
                  meetsPasswordPolicy(value)
                    ? true
                    : "Password does not meet the required policy",
              })}
            />
            <button
              type="button"
              className="btn-outline"
              onClick={() => setShowPassword((previous) => !previous)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          <p className="text-sm text-neutral-600">
            Strength: <span className="font-semibold capitalize">{passwordStrength.label}</span>
          </p>
          {errors.password && (
            <p id="register-password-error" className="text-sm text-red-600">
              {errors.password.message}
            </p>
          )}
        </div>

        <div className="space-y-1">
          <label htmlFor="register-confirm-password" className="font-medium text-neutral-700">
            Confirm Password
          </label>
          <div className="flex gap-2">
            <input
              id="register-confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              className="w-full border border-neutral-300 rounded-lg px-3 py-2"
              aria-invalid={Boolean(errors.confirmPassword)}
              aria-describedby={
                errors.confirmPassword ? "register-confirm-password-error" : undefined
              }
              {...register("confirmPassword", {
                required: "Please confirm your password",
                validate: (value) => value === password || "Passwords do not match",
              })}
            />
            <button
              type="button"
              className="btn-outline"
              onClick={() => setShowConfirmPassword((previous) => !previous)}
            >
              {showConfirmPassword ? "Hide" : "Show"}
            </button>
          </div>
          {errors.confirmPassword && (
            <p id="register-confirm-password-error" className="text-sm text-red-600">
              {errors.confirmPassword.message}
            </p>
          )}
        </div>

        <div className="space-y-1 text-sm text-neutral-700">
          <p className="font-medium">Password requirements</p>
          <ul className="list-disc list-inside">
            {PASSWORD_REQUIREMENTS.map((requirement) => (
              <li key={requirement}>{requirement}</li>
            ))}
          </ul>
        </div>

        <div className="space-y-1 text-sm text-neutral-700">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              aria-invalid={Boolean(errors.acceptTerms)}
              aria-describedby={errors.acceptTerms ? "register-terms-error" : undefined}
              {...register("acceptTerms", {
                validate: (value) => value || "You must accept the Terms of Service",
              })}
            />
            I accept the
            <a href="/terms" target="_blank" rel="noreferrer" className="underline">
              Terms of Service
            </a>
          </label>
          {errors.acceptTerms && (
            <p id="register-terms-error" className="text-sm text-red-600">
              {errors.acceptTerms.message}
            </p>
          )}

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              aria-invalid={Boolean(errors.acceptPrivacy)}
              aria-describedby={errors.acceptPrivacy ? "register-privacy-error" : undefined}
              {...register("acceptPrivacy", {
                validate: (value) => value || "You must accept the Privacy Policy",
              })}
            />
            I accept the
            <a href="/privacy" target="_blank" rel="noreferrer" className="underline">
              Privacy Policy
            </a>
          </label>
          {errors.acceptPrivacy && (
            <p id="register-privacy-error" className="text-sm text-red-600">
              {errors.acceptPrivacy.message}
            </p>
          )}
        </div>

        {formError && (
          <p className="text-sm text-red-600" role="alert">
            {formError}
          </p>
        )}

        <button type="submit" className="btn-primary w-full" disabled={!isValid || isSubmitting}>
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="text-sm text-neutral-700">
        Already have an account? <Link to="/login">Go to login</Link>
      </p>
    </section>
  );
}
