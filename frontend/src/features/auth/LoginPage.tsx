import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { getErrorMessage } from "../../shared/api";
import { AuthLayout } from "./AuthLayout";
import { useLogin } from "./session";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email."),
  password: z.string().min(1, "Password is required."),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const login = useLogin();
  const navigate = useNavigate();
  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  async function onSubmit(values: LoginForm) {
    try {
      await login.mutateAsync(values);
      navigate("/app", { replace: true });
    } catch {
      // React Query exposes the safe API error through mutation state.
    }
  }

  return (
    <AuthLayout title="Log in" subtitle="Access your OpsDesk workspace shell.">
      <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
        <div>
          <label htmlFor="email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("email")}
          />
          {form.formState.errors.email ? (
            <p className="mt-1 text-sm text-accent">
              {form.formState.errors.email.message}
            </p>
          ) : null}
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("password")}
          />
          {form.formState.errors.password ? (
            <p className="mt-1 text-sm text-accent">
              {form.formState.errors.password.message}
            </p>
          ) : null}
        </div>
        {login.isError ? (
          <p
            role="alert"
            className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
          >
            {getErrorMessage(login.error)}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={login.isPending}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <LogIn aria-hidden="true" className="h-4 w-4" />
          {login.isPending ? "Logging in" : "Log in"}
        </button>
      </form>
      <p className="mt-5 text-sm text-muted">
        New to OpsDesk?{" "}
        <Link to="/signup" className="font-semibold text-brand">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
