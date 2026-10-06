import { useEffect } from 'react';

export default function AtlasHome() {
  useEffect(() => {
    window.location.replace('/atlas/index.html');
  }, []);
  return <a href="/atlas/index.html">Open the Climbing Popularity Atlas</a>;
}
