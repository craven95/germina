import Link from "next/link";

export default function NoQuestionnairePrompt() {
  return (
    <section className="container mx-auto px-6 py-16 text-center">
      <h1 className="text-4xl font-extrabold mb-6 text-gray-900 dark:text-gray-100">
        Vous n'avez pas encore de questionnaire !
      </h1>
      <p className="text-lg text-gray-600 dark:text-gray-300 mb-10">
        Commencez par créer votre premier questionnaire personnalisé.
      </p>

      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow max-w-xl mx-auto">
        <div className="flex items-center justify-center mb-4">
          <svg
            className="w-12 h-12 text-indigo-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeWidth={2} d="M9 12h6m-3-3v6m9-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-2xl font-semibold mb-2 dark:text-gray-100">
          Créez un questionnaire
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Ajoutez des champs comme <strong>Nom</strong>, <strong>Prénom</strong>, <strong>Âge</strong>, <strong>Sexe</strong>...
        </p>
        <Link
          href="/protected/questionnaire/new"
          className="inline-block px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition"
        >
          Commencer
        </Link>
      </div>
    </section>
  );
}
