"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Assistant" },
  { href: "/documents", label: "Documents" },
  { href: "/study", label: "Study" },
  { href: "/research", label: "Research" },
  { href: "/coding", label: "Coding" },
  { href: "/career", label: "Career" },
  { href: "/calendar", label: "Calendar" },
  { href: "/announcements", label: "Campus" },
  { href: "/search", label: "Search" },
];

export function WorkspaceNav() {
  const pathname = usePathname();
  const { hasRole } = useAuth();
  const links = hasRole("ADMIN", "SUPER_ADMIN")
    ? [...LINKS, { href: "/admin", label: "Admin" }]
    : LINKS;
  return (
    <nav className="mb-8 flex flex-wrap gap-2 overflow-x-auto">
      {links.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={
              active
                ? "rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground"
                : "rounded-lg border px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted"
            }
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
