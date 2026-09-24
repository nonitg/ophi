// Inline JSON-LD structured data. Out of the way of the visible page, read by search engines.
import type { ReactElement } from "react";

// Escapes "<" so no data value can close the script block early.
export function JsonLd({ data }: { data: object }): ReactElement {
  const json = JSON.stringify(data).replace(/</g, "\\u003c");
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: json }} />;
}