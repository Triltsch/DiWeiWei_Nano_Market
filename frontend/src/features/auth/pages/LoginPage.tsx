import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../AuthContext";

interface LoginFormValues {
  email: string;
  password: string;
  rememberMe: boolean;
}

const REMEMBERED_EMAIL_KEY = "auth_remembered_email";

export function LoginPage(): JSX.Element {
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

  const redirectTarget = searchParams.get("redirect") ?? "/dashboard";

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
      const message = error instanceof Error ? error.message : "Login failed.";
      setFormError(message);
    }
  });

  return (
    <section className="card-elevated max-w-xl mx-auto space-y-4">
      <h1 className="text-primary-600">Login</h1>
      <p className="text-neutral-600">Welcome back. Please sign in to continue.</p>

      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-1">
          <label htmlFor="login-email" className="font-medium text-neutral-700">
            Email
          </label>
          <input
            id="login-email"
            type="email"
            className="w-full border border-neutral-300 rounded-lg px-3 py-2"
            {...register("email", {
              required: "Email is required",
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: "Please enter a valid email address",
              },
            })}
          />
          {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}
        </div>

        <div className="space-y-1">
          <label htmlFor="login-password" className="font-medium text-neutral-700">
            Password
          </label>
          <div className="flex gap-2">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              className="w-full border border-neutral-300 rounded-lg px-3 py-2"
              {...register("password", {
                required: "Password is required",
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
          {errors.password && <p className="text-sm text-red-600">{errors.password.message}</p>}
        </div>

        <label className="flex items-center gap-2 text-sm text-neutral-700">
          <input type="checkbox" {...register("rememberMe")} />
          Remember my email
        </label>

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <button type="submit" className="btn-primary w-full" disabled={!isValid || isSubmitting}>
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <div className="text-sm text-neutral-700 space-y-2">
        <p>
          <a href="/faq" className="underline">
            Forgot password? (Coming soon)
          </a>
        </p>
        <p>
          Don&apos;t have an account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </section>
  );
}
