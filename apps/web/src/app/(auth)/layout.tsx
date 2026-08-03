export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 px-4">
      <div className="mb-8 flex items-center gap-2">
        <span className="text-lg font-semibold tracking-tight">Scrum Tool</span>
      </div>
      {children}
    </div>
  );
}
