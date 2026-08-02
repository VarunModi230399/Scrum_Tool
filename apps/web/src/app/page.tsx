import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ThemeToggle } from "@/components/shared/theme-toggle";

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-16">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold tracking-tight">Scrum Tool</span>
          <Badge variant="secondary">Phase 1</Badge>
        </div>
        <ThemeToggle />
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Foundation skeleton</CardTitle>
          <CardDescription>
            Next.js, Tailwind, shadcn/ui, React Query, and dark mode are wired up. Feature
            modules land here as Phase 1 work proceeds.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Button>Primary action</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
        </CardContent>
      </Card>
    </div>
  );
}
