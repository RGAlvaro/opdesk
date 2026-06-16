import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { getErrorMessage } from "../../shared/api";
import { AuthLayout } from "./AuthLayout";
import { useSignup } from "./session";

const passwordSchema = z
  .string()
  .min(10, "Password must be at least 10 characters.")
  .regex(/[A-Za-z]/, "Password must include a letter.")
  .regex(/[0-9]/, "Password must include a number.");

const signupSchema = z.object({
  full_name: z.string().trim().min(1, "Full name is required.").max(120),
  email: z.string().email("Enter a valid email."),
  password: passwordSchema,
});

type SignupForm = z.infer<typeof signupSchema>;

export function SignupPage() {
  const signup = useSignup();
  const navigate = useNavigate();
  const form = useForm<SignupForm>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
    },
  });

  async function onSubmit(values: SignupForm) {
    try {
      await signup.mutateAsync({
        ...values,
        full_name: values.full_name.trim(),
      });
      navigate("/app", { replace: true });
    } catch {
      // React Query exposes the safe API error through mutation state.
    }
  }

  return (
    <AuthLayout title="Create account" subtitle="Start with your user profile.">
      <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
        <div>
          <label htmlFor="full_name" className="block text-sm font-medium">
            Full name
          </label>
          <input
            id="full_name"
            type="text"
            autoComplete="name"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("full_name")}
          />
          {form.formState.errors.full_name ? (
            <p className="mt-1 text-sm text-accent">
              {form.formState.errors.full_name.message}
            </p>
          ) : null}
        </div>
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
            autoComplete="new-password"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("password")}
          />
          {form.formState.errors.password ? (
            <p className="mt-1 text-sm text-accent">
              {form.formState.errors.password.message}
            </p>
          ) : null}
        </div>
        {signup.isError ? (
          <p
            role="alert"
            className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
          >
            {getErrorMessage(signup.error)}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={signup.isPending}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <UserPlus aria-hidden="true" className="h-4 w-4" />
          {signup.isPending ? "Creating account" : "Create account"}
        </button>
      </form>
      <p className="mt-5 text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-brand">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
