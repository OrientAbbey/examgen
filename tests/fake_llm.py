"""Faux fournisseur d'IA pour les tests et le test navigateur : aucun réseau, aucune clé.
Protocoles : OpenAI (/v1/chat/completions) et Anthropic (/v1/messages). Réponses scriptables, sinon réponses « de démonstration »
déterministes selon la ligne « ACTION: … » du message. Usage autonome : python tests/fake_llm.py PORT"""
import json
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CATALOGUE = re.compile(r"<catalogue>\n(.*?)\n</catalogue>", re.S)


def _catalogue(user):
    return json.loads(CATALOGUE.search(user).group(1))


def auto(system: str, user: str) -> str:
    m = re.search(r"^ACTION: (\w+)", user, re.M)
    action = m.group(1) if m else "?"
    if action == "test":
        return "OK"
    if action == "generer":
        return ("=== SUJET ===\nSoit $(u_n)$ la suite géométrique de premier terme $u_0 = 3$ et de raison $q = 2$.\n\n1. Calculer $u_1$ et $u_2$.\n2. Exprimer $u_n$ en fonction de $n$.\n"
                "=== CORRIGE ===\nSolution :\n\n1. $u_1 = 6$ et $u_2 = 12$.\n2. $u_n = 3 \\times 2^{n}$.\n=== NIVEAU ===\nFacile\n")
    if action == "verifier":
        if "ERREUR" in user:
            return ("=== VERDICT ===\nproblemes\n=== PROBLEMES ===\n- Question 1 : $u_1$ vaut 6 et non 5.\n- Question 2 : exposant incorrect.\n"
                    "=== CORRIGE_CORRIGE ===\nSolution :\n\n1. $u_1 = 6$.\n2. $u_n = 3 \\times 2^{n}$.\n")
        return "=== VERDICT ===\nok\n=== PROBLEMES ===\n"
    if action in ("convertir", "reparer"):
        return ("=== SUJET ===\nSoit $f(x) = x^{2} + 1$. Calculer $f(2)$.\n=== CORRIGE ===\nSolution :\n$f(2) = 5$.\n=== MODIFICATIONS ===\n- Symboles Unicode remplacés par du LaTeX.\n- Virgule décimale corrigée.\n")
    if action == "variantes":
        n = int(re.search(r"Nombre de variantes : (\d+)", user).group(1))
        return "".join("=== SUJET ===\nSoit $f(x) = %dx + 1$. Calculer $f(%d)$.\n=== CORRIGE ===\nSolution :\n$f(%d) = %d$.\n" % (i + 2, i + 1, i + 1, (i + 2) * (i + 1) + 1) for i in range(n))
    if action == "metadonnees":
        c = _catalogue(user)
        return ("=== NIVEAU ===\nMoyen\n=== SESSION ===\n3\n=== PARTIE_ID ===\n%s\n=== CLASSE_IDS ===\n%s\n=== TAG_EXAMEN ===\nnon\n=== JUSTIFICATION ===\nExercice classique de séquence 3.\n"
                % (c["parties"][0]["id"] if c["parties"] else "", ",".join(x["id"] for x in c["classes"][:2])))
    if action == "parametres":
        c = _catalogue(user)
        pick = lambda cle, mot: next((x["id"] for x in c[cle] if mot.lower() in x["nom"].lower()), None)
        return json.dumps({"matiereId": pick("matieres", "math") or (c["matieres"][0]["id"] if c["matieres"] else None), "classeId": pick("classes", "terminale"), "specialiteId": pick("specialites", "Mathématiques"),
                           "session": "3", "difficulte": "Moyen", "explication": "Épreuve de mathématiques de Terminale, séquence 3, difficulté moyenne."}, ensure_ascii=False)
    if action == "bareme":
        n = int(re.search(r"Nombre d'exercices : (\d+)", user).group(1))
        par = 20 / n
        return json.dumps({"dureeMinutes": 60, "exercices": [{"numero": i + 1, "points": par, "questions": [{"q": "1", "points": par / 2}, {"q": "2", "points": par / 2}]} for i in range(n)],
                           "remarques": "Barème indicatif sur 20 points."}, ensure_ascii=False)
    return "réponse inattendue"


class FakeLLM:
    def __init__(self, port: int = 0):
        self.requests, self.queue = [], []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                corps = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or 0) or b"{}")
                anth = self.path.endswith("/v1/messages")
                system = corps.get("system", "") if anth else corps["messages"][0]["content"]
                user = corps["messages"][0]["content"] if anth else corps["messages"][1]["content"]
                outer.requests.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": corps, "system": system, "user": user})
                rep = outer.queue.pop(0) if outer.queue else auto(system, user)
                if isinstance(rep, tuple) and rep[0] == "http":
                    self._envoyer(rep[1], {"error": {"message": "erreur simulée %d" % rep[1]}})
                    return
                if isinstance(rep, tuple) and rep[0] == "lent":
                    time.sleep(rep[1])
                    rep = "trop tard"
                self._envoyer(200, {"content": [{"type": "text", "text": rep}]} if anth else {"choices": [{"message": {"content": rep}}]})

            def _envoyer(self, code, obj):
                data = json.dumps(obj).encode("utf-8")
                try:
                    self.send_response(code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except OSError:
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", port), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @property
    def url(self):
        return "http://127.0.0.1:%d" % self.port

    def script(self, *reponses):
        self.queue.extend(reponses)

    def reset(self):
        self.requests.clear()
        self.queue.clear()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


if __name__ == "__main__":
    f = FakeLLM(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print("Faux fournisseur d'IA sur", f.url, flush=True)
    threading.Event().wait()
