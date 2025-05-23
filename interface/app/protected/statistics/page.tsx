'use client';

import { useState, useEffect } from 'react';
import { createClient } from '@/utils/supabase/client';
import Papa from 'papaparse';
import { ArrowLeft, UploadCloud, CloudRain } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Lottie from 'lottie-react';
import waveAnimation from '../../../components/animations/cat_waiting.json';

export default function StatisticsPage() {
  const router = useRouter();
  const supabase = createClient();

  const [csvData, setCsvData] = useState<any[]>([]);
  const [stats, setStats] = useState<Record<string, { min: number; max: number; mean: number }>>({});
  const [error, setError] = useState<string | null>(null);


  const analyze = (data: any[]) => {
    const numericCols: Record<string, number[]> = {};
    data.forEach(row => {
      Object.entries(row).forEach(([key, value]) => {
        const num = parseFloat(value);
        if (!isNaN(num)) {
          numericCols[key] = numericCols[key] || [];
          numericCols[key].push(num);
        }
      });
    });
    const result: Record<string, any> = {};
    Object.entries(numericCols).forEach(([col, vals]) => {
      const sum = vals.reduce((a, b) => a + b, 0);
      result[col] = {
        min: Math.min(...vals),
        max: Math.max(...vals),
        mean: sum / vals.length,
      };
    });
    setStats(result);
  };

  const handleFile = (file: File) => {
    setError(null);
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        setCsvData(results.data as any[]);
        analyze(results.data as any[]);
      },
      error: (err) => setError(err.message),
    });
  };

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
          <input
            type="file"
            accept=".csv"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 p-2 rounded w-full"
          />
        </div>

        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-gray-100">
            <CloudRain /> Extraire depuis un déploiement cloud
          </h2>
        </div>

        {error && (
          <div className="text-red-600 dark:text-red-400">⚠️ {error}</div>
        )}

        {Object.keys(stats).length > 0 && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
              Résumé statistique
            </h2>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr>
                  <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100">Colonne</th>
                  <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100">Min</th>
                  <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100">Max</th>
                  <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100">Moyenne</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats).map(([col, { min, max, mean }]) => (
                  <tr key={col}>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-gray-900 dark:text-gray-100">{col}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-gray-900 dark:text-gray-100">{min.toFixed(2)}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-gray-900 dark:text-gray-100">{max.toFixed(2)}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-gray-900 dark:text-gray-100">{mean.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
