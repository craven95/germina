'use client';

import { UploadCloud, CloudRain } from 'lucide-react';
import Lottie from 'lottie-react';
import waveAnimation from '../../../components/animations/cat_waiting.json';

export default function StatisticsPage() {

  return (
    <section className="container mx-auto px-6 py-12 max-w-3xl">
      <div className="flex items-center">
      <div className="w-20 h-20"><Lottie animationData={waveAnimation} loop /></div>
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-gray-100">
        Chantier en cours...
      </h1>
    </div>
      <div className="space-y-6">
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-gray-100">
            <UploadCloud /> Importer un fichier CSV
          </h2>
        </div>

        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-gray-100">
            <CloudRain /> Extraire depuis un déploiement cloud
          </h2>
        </div>

      </div>
    </section>
  );
}
