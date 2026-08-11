// Profile page for viewing and updating the authenticated user's own details.

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { UseFormRegisterReturn, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { ApiError, apiRequest, getErrorMessage } from "../../shared/api";
import { sessionQueryKey, useSession } from "../auth/session";
import { User } from "../auth/types";

const profileSchema = z.object({
  full_name: z.string().trim().min(1, "Full name is required.").max(120),
  email: z.string().trim().email("Email must be valid.").max(320),
  current_password: z.string().optional(),
  job_title: z.string().trim().max(120).optional(),
  phone: z.string().trim().max(40).optional(),
  timezone: z.string().trim().max(120).optional(),
  locale: z.string().trim().max(40).optional(),
  avatar_url: z
    .string()
    .trim()
    .url("Avatar URL must be valid.")
    .optional()
    .or(z.literal("")),
  bio: z.string().trim().max(1000).optional(),
});

type ProfileForm = z.infer<typeof profileSchema>;

/** Render the current user's profile summary and editable full-name form. */
export function ProfilePage() {
  const session = useSession();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const form = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      email: "",
      current_password: "",
      job_title: "",
      phone: "",
      timezone: "",
      locale: "",
      avatar_url: "",
      bio: "",
    },
  });

  useEffect(() => {
    if (session.data) {
      form.reset({
        full_name: session.data.full_name,
        email: session.data.email,
        current_password: "",
        job_title: session.data.job_title ?? "",
        phone: session.data.phone ?? "",
        timezone: session.data.timezone ?? "",
        locale: session.data.locale ?? "",
        avatar_url: session.data.avatar_url ?? "",
        bio: session.data.bio ?? "",
      });
    }
  }, [form, session.data]);

  const updateProfile = useMutation({
    mutationFn: (payload: ProfileForm) =>
      apiRequest<User>("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify(profilePayload(payload, session.data?.email)),
      }),
    onSuccess: (user) => {
      queryClient.setQueryData(sessionQueryKey, user);
      form.reset({
        full_name: user.full_name,
        email: user.email,
        current_password: "",
        job_title: user.job_title ?? "",
        phone: user.phone ?? "",
        timezone: user.timezone ?? "",
        locale: user.locale ?? "",
        avatar_url: user.avatar_url ?? "",
        bio: user.bio ?? "",
      });
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 401) {
        queryClient.removeQueries({ queryKey: sessionQueryKey });
        navigate("/login", { replace: true });
      }
    },
  });

  /** Persist profile edits through the current-user API endpoint. */
  async function onSubmit(values: ProfileForm) {
    try {
      await updateProfile.mutateAsync(values);
    } catch {
      // React Query exposes the safe API error through mutation state.
    }
  }

  return (
    <section className="max-w-2xl rounded-md border border-line bg-white p-6 shadow-panel">
      <h1 className="text-2xl font-semibold">Profile</h1>
      <p className="mt-2 text-sm text-muted">Manage your own user details.</p>

      <dl className="mt-6 grid gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-sm font-medium text-muted">Email</dt>
          <dd className="mt-1 font-medium">{session.data?.email}</dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-muted">Account status</dt>
          <dd className="mt-1 font-medium">
            {session.data?.is_active ? "Active" : "Inactive"}
          </dd>
        </div>
      </dl>

      <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
        <div className="grid gap-4 sm:grid-cols-2">
          <ProfileInput
            id="profile_full_name"
            label="Full name"
            autoComplete="name"
            registration={form.register("full_name")}
            error={form.formState.errors.full_name?.message}
          />
          <ProfileInput
            id="profile_email"
            label="Email"
            type="email"
            autoComplete="email"
            registration={form.register("email")}
            error={form.formState.errors.email?.message}
          />
          <ProfileInput
            id="profile_current_password"
            label="Current password"
            type="password"
            autoComplete="current-password"
            registration={form.register("current_password")}
            error={form.formState.errors.current_password?.message}
          />
          <ProfileInput
            id="profile_job_title"
            label="Job title"
            registration={form.register("job_title")}
            error={form.formState.errors.job_title?.message}
          />
          <ProfileInput
            id="profile_phone"
            label="Phone"
            autoComplete="tel"
            registration={form.register("phone")}
            error={form.formState.errors.phone?.message}
          />
          <ProfileInput
            id="profile_timezone"
            label="Timezone"
            registration={form.register("timezone")}
            error={form.formState.errors.timezone?.message}
          />
          <ProfileInput
            id="profile_locale"
            label="Locale"
            registration={form.register("locale")}
            error={form.formState.errors.locale?.message}
          />
          <ProfileInput
            id="profile_avatar_url"
            label="Avatar URL"
            type="url"
            registration={form.register("avatar_url")}
            error={form.formState.errors.avatar_url?.message}
          />
        </div>
        <div>
          <label htmlFor="profile_bio" className="block text-sm font-medium">
            Bio
          </label>
          <textarea
            id="profile_bio"
            className="mt-1 min-h-28 w-full rounded-md border border-line px-3 py-2"
            {...form.register("bio")}
          />
          {form.formState.errors.bio ? (
            <p className="mt-1 text-sm text-accent">
              {form.formState.errors.bio.message}
            </p>
          ) : null}
        </div>
        {updateProfile.isError ? (
          <p
            role="alert"
            className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
          >
            {getErrorMessage(updateProfile.error)}
          </p>
        ) : null}
        {updateProfile.isSuccess ? (
          <p
            role="status"
            className="rounded-md bg-green-50 px-3 py-2 text-sm text-brand"
          >
            Profile updated.
          </p>
        ) : null}
        <button
          type="submit"
          disabled={updateProfile.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <Save aria-hidden="true" className="h-4 w-4" />
          {updateProfile.isPending ? "Saving" : "Save changes"}
        </button>
      </form>
    </section>
  );
}

/** Trim optional form text and use null for blank metadata fields. */
function optionalText(value: string | undefined) {
  const trimmed = value?.trim() ?? "";
  return trimmed ? trimmed : null;
}

/** Build the current-user update payload without returning password data. */
function profilePayload(values: ProfileForm, currentEmail: string | undefined) {
  const nextEmail = values.email.trim();
  return {
    full_name: values.full_name.trim(),
    email: nextEmail,
    ...(nextEmail !== currentEmail && values.current_password
      ? { current_password: values.current_password }
      : {}),
    job_title: optionalText(values.job_title),
    phone: optionalText(values.phone),
    timezone: optionalText(values.timezone),
    locale: optionalText(values.locale),
    avatar_url: optionalText(values.avatar_url),
    bio: optionalText(values.bio),
  };
}

/** Render one profile input with shared error presentation. */
function ProfileInput({
  id,
  label,
  registration,
  error,
  type = "text",
  autoComplete,
}: {
  id: string;
  label: string;
  registration: UseFormRegisterReturn;
  error: string | undefined;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        type={type}
        autoComplete={autoComplete}
        className="mt-1 w-full rounded-md border border-line px-3 py-2"
        {...registration}
      />
      {error ? <p className="mt-1 text-sm text-accent">{error}</p> : null}
    </div>
  );
}
