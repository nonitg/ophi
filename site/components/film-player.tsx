"use client";

import { useRef, useState, useSyncExternalStore } from "react";

const subscribeNever = () => () => {};

// The film behind one obvious play button. Nothing of it downloads until play: the poster holds its place,
// so the page stays as light as its text. Before hydration the browser's own controls do the job.
export function FilmPlayer({ src, poster, length }: { src: string; poster: string; length: string }) {
  const video = useRef<HTMLVideoElement>(null);
  const [started, setStarted] = useState(false);
  const enhanced = useSyncExternalStore(subscribeNever, () => true, () => false);

  return (
    <div className="film relative mt-8 overflow-hidden rounded-[28px] bg-ink phone:mt-6 phone:rounded-[16px]">
      <video ref={video} className="block aspect-video w-full" controls={!enhanced || started} playsInline preload="none" poster={poster} width={1920} height={1080} aria-label="Ophi, the film" onPlay={() => setStarted(true)}>
        <source src={src} type="video/mp4" />
      </video>
      {enhanced && !started && (
        <button type="button" className="group/play absolute inset-0 grid place-items-center focus-visible:outline-offset-[-6px]" onClick={() => { setStarted(true); void video.current?.play(); }}>
          <span className="inline-flex h-[58px] items-center gap-3 rounded-full bg-orange pr-6 pl-5 text-[14px] font-medium text-ink shadow-[0_14px_40px_-10px_#00000080] transition-[background,scale] duration-250 group-hover/play:scale-[1.04] group-hover/play:bg-[#f59973] phone:h-[50px] phone:pr-5 phone:pl-4 phone:text-[13px]">
            <svg viewBox="0 0 20 20" className="size-5" fill="currentColor" aria-hidden="true"><path d="M6.5 4.3v11.4a.6.6 0 0 0 .9.5l9.2-5.7a.6.6 0 0 0 0-1L7.4 3.8a.6.6 0 0 0-.9.5Z" /></svg>
            Play the film
            <span className="text-[12px] opacity-70">{length}</span>
          </span>
        </button>
      )}
    </div>
  );
}
