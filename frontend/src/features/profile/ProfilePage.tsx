// Profile page for viewing and updating the authenticated user's own details.

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { ApiError, apiRequest, getErrorMessage } from "../../shared/api";
import { sessionQueryKey, useSession } from "../auth/session";
import { User } from "../auth/types";

const profileSchema = z.object({
  full_name: z.string().trim().min(1, "Full name is required.").max(120),
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
    },
  });

  useEffect(() => {
    if (session.data) {
      form.reset({ full_name: session.data.full_name });
    }
  }, [form, session.data]);

  const updateProfile = useMutation({
    mutationFn: (payload: ProfileForm) =>
      apiRequest<User>("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({ full_name: payload.full_name.trim() }),
      }),
    onSuccess: (user) => {
      queryClient.setQueryData(sessionQueryKey, user);
      form.reset({ full_name: user.full_name });
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
        <div>
          <label
            htmlFor="profile_full_name"
            className="block text-sm font-medium"
          >
            Full name
          </label>
          <input
            id="profile_full_name"
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
