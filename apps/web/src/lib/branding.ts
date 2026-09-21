/** Single place to rebrand the product. Nothing else hard-codes the name. */
export const branding = {
  name: process.env.NEXT_PUBLIC_APP_NAME ?? "UniOS AI",
  shortName: "UniOS",
  tagline: "One intelligent system for your entire university life.",
  heroLine: "Your university's intelligent operating system.",
} as const;
