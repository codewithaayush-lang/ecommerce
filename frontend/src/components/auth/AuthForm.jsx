"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { buttonStyles } from "@/components/ui/buttonStyles";

function SubmitButton({ label }) {
  // `useFormStatus` must be read in a child of the <form> so it reflects that
  // form's pending state.
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className={`${buttonStyles({ size: "lg" })} w-full`}
    >
      {pending ? "Please wait…" : label}
    </button>
  );
}

function Field({ id, label, error, children }) {
  return (
    <div>
      <label
        htmlFor={id}
        className="block text-sm font-medium text-stone-700"
      >
        {label}
      </label>
      <div className="mt-1.5">{children}</div>
      {error ? (
        <p id={`${id}-error`} className="mt-1.5 text-sm text-red-600">
          {error}
        </p>
      ) : null}
    </div>
  );
}

const inputClasses =
  "w-full rounded-md border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-900 transition-colors placeholder:text-stone-400 hover:border-stone-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-200 focus:outline-none";

/**
 * Shared login/register form.
 *
 * The only Client Component needed for authentication: `useActionState` runs
 * the Server Action and surfaces its returned error state, so validation
 * messages come from Django without any client-side duplication of the rules.
 */
export default function AuthForm({ mode, action, submitLabel, footer }) {
  const [state, formAction] = useActionState(action, { error: null, fields: {} });
  const isRegister = mode === "register";

  return (
    <form action={formAction} className="space-y-5" noValidate>
      {state?.error ? (
        <p
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
        >
          {state.error}
        </p>
      ) : null}

      <Field id="username" label="Username" error={state?.fields?.username}>
        <input
          id="username"
          name="username"
          type="text"
          autoComplete="username"
          required
          aria-invalid={state?.fields?.username ? "true" : undefined}
          aria-describedby={
            state?.fields?.username ? "username-error" : undefined
          }
          className={inputClasses}
        />
      </Field>

      {isRegister ? (
        <Field id="email" label="Email" error={state?.fields?.email}>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            aria-invalid={state?.fields?.email ? "true" : undefined}
            aria-describedby={state?.fields?.email ? "email-error" : undefined}
            className={inputClasses}
          />
        </Field>
      ) : null}

      <Field id="password" label="Password" error={state?.fields?.password}>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete={isRegister ? "new-password" : "current-password"}
          required
          aria-invalid={state?.fields?.password ? "true" : undefined}
          aria-describedby={
            state?.fields?.password ? "password-error" : undefined
          }
          className={inputClasses}
        />
      </Field>

      {isRegister ? (
        <Field
          id="confirm_password"
          label="Confirm password"
          error={state?.fields?.confirm_password}
        >
          <input
            id="confirm_password"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            required
            className={inputClasses}
          />
        </Field>
      ) : null}

      <SubmitButton label={submitLabel} />

      {footer}
    </form>
  );
}
