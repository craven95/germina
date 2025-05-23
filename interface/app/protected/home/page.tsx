import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";

export default async function ProtectedPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return redirect("/sign-in");
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const { data: questionnaires } = await supabase
    .from("questionnaires")
    .select("id, title, created_at")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  const hasQuestionnaire = questionnaires && questionnaires.length > 0;

  return (
    <section className="container mx-auto px-6 py-16 text-center">
      <h1 className="text-4xl font-extrabold mb-6 text-gray-900 dark:text-gray-100">
        {hasQuestionnaire
          ? "Bien joué !"
          : "Vous n'avez pas encore de questionnaire !"}
      </h1>

      <p className="text-lg text-gray-600 dark:text-gray-300 mb-10">
        {hasQuestionnaire ? (
          <>Vous avez déjà créé au moins 1 questionnaire. Maintenant, déployez-le pour commencer à collecter des données !</>
        ) : (
          <>Créez-en vite un en suivant les deux étapes ci-dessous : définir les données à collecter, puis déployer votre questionnaire.</>
        )}
      </p>

      <div className={`grid gap-8 ${hasQuestionnaire ? 'md:grid-cols-1' : 'md:grid-cols-2'}`}>
        {!hasQuestionnaire && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-center mb-4">
              <svg
                className="w-12 h-12 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeWidth={2} d="M9 12h6m-3-3v6m9-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold mb-2 dark:text-gray-100">
              Étape 1 : Créez votre questionnaire
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              Choisissez les champs à collecter : <strong>Nom, Prénom, Âge, Sexe, Rapports, Photos</strong>, etc.
            </p>
            <a
              href="/protected/questionnaire"
              className="inline-block px-6 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition"
            >
              Commencer
            </a>
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-center mb-4">
            <svg
              className="w-12 h-12 text-indigo-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold mb-2 dark:text-gray-100">
            Étape 2 : Déployez votre questionnaire
          </h2>
          <div className="text-gray-600 dark:text-gray-300 mb-4 text-left">
            <p>Hébergez-le partout :</p>
            <ul className="list-disc list-inside mt-2">
              <li>En local sur votre machine</li>
              <li>Sur une VM privée sécurisée</li>
              <li>Sur la VM de votre hôpital</li>
            </ul>
            <p>Choisissez l'accès : public ou restreint en local.</p>
          </div>
          <a
            href="/protected/deploiement"
            className="inline-block px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition"
          >
            Déployer
          </a>
        </div>
      </div>
    </section>
  );
}
