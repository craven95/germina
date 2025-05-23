'use client';

import { ThemeSwitcher } from '@/components/theme-switcher';

export default function Footer() {
  return (
    <footer className="w-full flex items-center justify-center border-t mx-auto text-center text-xs gap-8 py-16">
      <p>
        Powered by{' '}
        <a
          href="https://www.linkedin.com/in/craven-diot/"
          target="_blank"
          className="font-bold hover:underline"
          rel="noreferrer"
        >
          Craven
        </a>
      </p>
      <ThemeSwitcher />
    </footer>
  );
}
