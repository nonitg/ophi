import { heading, lede as ledeType } from "@/components/type";

// Every section opens the same way: one heading that carries the idea, one sentence under it.
export function SectionHead({ id, title, lede }: { id: string; title: string; lede?: string }) {
  return (
    <div data-reveal className="max-w-[860px]">
      <h2 id={id} className={heading}>{title}</h2>
      {lede && <p className={`${ledeType} mt-6 max-w-[620px]`}>{lede}</p>}
    </div>
  );
}
