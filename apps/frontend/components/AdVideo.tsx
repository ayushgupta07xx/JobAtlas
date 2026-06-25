'use client';

import { useEffect, useState } from 'react';

const AD_LANDSCAPE = 'https://pub-7d6092403e9d4518920d52f3fb6f2593.r2.dev/ad/jobatlas-ad.mp4';
const AD_VERTICAL = 'https://pub-7d6092403e9d4518920d52f3fb6f2593.r2.dev/ad/jobatlas-ad-vertical.mp4';
const POSTER = '/ad/poster.jpg';
const PORTRAIT = '(orientation: portrait), (max-width: 700px)';

export default function AdVideo() {
  const [portrait, setPortrait] = useState<boolean | null>(null);

  useEffect(() => {
    const mq = window.matchMedia(PORTRAIT);
    const update = () => setPortrait(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

  if (portrait === null) {
    return (
      <div style={{ width: '100%', maxWidth: 960, aspectRatio: '16 / 9', margin: '0 auto' }} />
    );
  }

  const src = portrait ? AD_VERTICAL : AD_LANDSCAPE;

  return (
    <video
      key={src}
      src={src}
      poster={POSTER}
      autoPlay
      muted
      loop
      playsInline
      preload="metadata"
      style={{
        display: 'block',
        margin: '0 auto',
        width: '100%',
        maxWidth: portrait ? 420 : 960,
        borderRadius: 16,
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.18)',
      }}
    />
  );
}
