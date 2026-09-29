import Link from "next/link";
import { redirect } from "next/navigation";
import Container from "@/components/ui/Container";
import AuthForm from "@/components/auth/AuthForm";
import { getCurrentUser } from "@/lib/serverApi";
import { loginAction } from "@/app/actions";

export const metadata = {
  title: "Login",
};

export default async function LoginPage() {
  // An already signed-in visitor has no reason to see the login form.
  const user = await getCurrentUser();
  if (user) {
    redirect("/");
  }

  return (
    <Container>
      <div className="flex min-h-[60vh] items-center justify-center py-12">
        <div className="w-full max-w-md">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900">
            Sign in
          </h1>
          <p className="mt-2 text-stone-600">
            Sign in to manage your cart and orders.
          </p>

          <div className="mt-8">
            <AuthForm
              mode="login"
              action={loginAction}
              submitLabel="Sign in"
              footer={
                <p className="text-sm text-stone-600">
                  New here?{" "}
                  <Link
                    href="/register"
                    className="font-medium text-brand-700 underline underline-offset-4 hover:text-brand-900"
                  >
                    Create an account
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
