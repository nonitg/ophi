import type { MetadataRoute } from "next";
import { copy } from "@/lib/copy";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: copy.name,
    short_name: copy.name,
    description: copy.description,
    start_url: "/",
    display: "standalone",
    background_color: "#f4f2e9",
    theme_color: "#193a30",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}