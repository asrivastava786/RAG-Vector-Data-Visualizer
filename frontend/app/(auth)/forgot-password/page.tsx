import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ForgotPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-5">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Password recovery</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Recovery email delivery is reserved for the production email integration phase.
          </p>
          <Link
            className="inline-flex h-10 items-center justify-center rounded-md bg-muted px-4 text-sm font-medium hover:bg-muted/80"
            href="/login"
          >
            Back to sign in
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
