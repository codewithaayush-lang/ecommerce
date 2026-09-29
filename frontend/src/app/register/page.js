import Link from "next/link";
import { redirect } from "next/navigation";
import Container from "@/components/ui/Container";
import AuthForm from "@/components/auth/AuthForm";
import { getCurrentUser } from "@/lib/serverApi";
import { registerAction } from "@/app/actions";

export const metadata = {
  title: "Create an account",
};

export default async function RegisterPage() {
  const user = await getCurrentUser();
  if (user) {
    redirect("/");
  }

  return (
    <Container>
      <div className="flex min-h-[60vh] items-center justify-center py-12">
        <div className="w-full max-w-md">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900">
            Create an account
          </h1>
          <p className="mt-2 text-stone-600">
            Register to keep a cart and track your orders.
          </p>

          <div className="mt-8">
            <AuthForm
              mode="register"
              action={registerAction}
              submitLabel="Create account"
              footer={
                <p className="text-sm text-stone-600">
                  Already have an account?{" "}
                  <Link
                    href="/login"
                    className="font-medium text-brand-700 underline underline-offset-4 hover:text-brand-900"
                  >
                    Sign in
                  </Link>
                </p>
              }
            />
          </div>
        </div>
      </div>
    </Container>
  );
}
