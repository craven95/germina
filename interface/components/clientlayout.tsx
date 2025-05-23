'use client';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import Link from 'next/link';
import {
  HomeIcon,
  DocumentTextIcon,
  ChartBarIcon,
  Bars3Icon as MenuIcon,
  XMarkIcon as XIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isProtected = pathname.startsWith('/protected');
  const [open, setOpen] = useState(true);
  const sidebarWidth = open ? 'w-64' : 'w-16';
  const contentMargin = isProtected ? (open ? 'ml-64' : 'ml-16') : 'ml-0';

  return (
    <div className="flex min-h-screen">
      {isProtected && (
        <aside
          className={`fixed top-0 left-0 h-screen bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-sm z-50 transition-width duration-300 ${sidebarWidth}`}
        >
          <div className="flex items-center justify-between h-16 border-b border-gray-200 dark:border-gray-700 px-4">
            {open && (
              <span className="text-xl font-semibold text-gray-800 dark:text-gray-100">
                Menu
              </span>
            )}
            <button
              onClick={() => setOpen(!open)}
              className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none"
              aria-label="Toggle sidebar"
            >
              {open ? <XIcon className="w-5 h-5 text-gray-800 dark:text-gray-100" /> : <MenuIcon className="w-5 h-5 text-gray-800 dark:text-gray-100" />}
            </button>
          </div>
          <nav className="flex flex-col p-2 space-y-1">
            <Link
              href="/protected/home"
              className={`flex items-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 ${
                pathname === '/protected/home' ? 'font-bold text-indigo-600 dark:text-indigo-400' : 'text-gray-700 dark:text-gray-200'
              }`}
            >
              <HomeIcon className="w-6 h-6" />
              {open && <span className="ml-2">Accueil</span>}
            </Link>

            <Link
              href="/protected/questionnaire"
              className={`flex items-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 ${
                pathname.startsWith('/protected/questionnaire') ? 'font-bold text-indigo-600 dark:text-indigo-400' : 'text-gray-700 dark:text-gray-200'
              }`}
            >
              <DocumentTextIcon className="w-6 h-6" />
              {open && <span className="ml-2">Questionnaires</span>}
            </Link>

            <Link
              href="/protected/deploiement"
              className={`flex items-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 ${
                pathname.startsWith('/protected/deploiement') ? 'font-bold text-indigo-600 dark:text-indigo-400' : 'text-gray-700 dark:text-gray-200'
              }`}
            >
              <RocketLaunchIcon className="w-6 h-6" />
              {open && <span className="ml-2">Déploiement</span>}
            </Link>

            <Link
              href="/protected/statistics"
              className={`flex items-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 ${
                pathname.startsWith('/protected/statistics') ? 'font-bold text-indigo-600 dark:text-indigo-400' : 'text-gray-700 dark:text-gray-200'
              }`}
            >
              <ChartBarIcon className="w-6 h-6" />
              {open && <span className="ml-2">Statistiques</span>}
            </Link>
          </nav>
        </aside>
      )}
      <div
        className={`${contentMargin} flex-1 flex flex-col justify-between min-h-screen`}
      >
        {children}
      </div>
    </div>
  );
}
