import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";
import NoQuestionnairePrompt from "@/components/noquestionnaire";
import QuestionnairesDeployHome from "@/components/questionairesdeployhome";

export default async function ProtectedPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return redirect("/sign-in");

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const { data: questionnaires, error } = await supabase
    .from("questionnaires")
    .select("id, title, created_at, schema_json")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Erreur lors de la récupération des questionnaires:", error);
    return <div>Erreur lors du chargement des questionnaires.</div>;
  }

  if (!questionnaires || questionnaires.length === 0) {
    return <NoQuestionnairePrompt />;
  }

  return <QuestionnairesDeployHome questionnaires={questionnaires} />;
}
