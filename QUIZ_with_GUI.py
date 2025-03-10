import streamlit as st
import random

# -------------------------------------
# Funktion zum Laden der Fragen aus der Textdatei
# -------------------------------------
def load_questions(filename):
    questions = []
    categories = []
    current_category = None
    question_id = 1
    question_lines = []  # Puffer für die Zeilen der aktuellen Frage

    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            
            # 1) Kategorie-Wechsel
            if line.startswith("Kategorie:"):
                # Neue Kategorie setzen
                current_category = line.split(":", 1)[1].strip()
                # Falls diese Kategorie noch nicht in der Liste ist, hinzufügen
                if current_category not in categories:
                    categories.append(current_category)

            # 2) Antwort-Zeile
            elif line.startswith("Antwort:"):
                # Antwort aus Zeile extrahieren
                answer = line.split("Antwort:", 1)[1].strip()
                # Frage bilden (alle gesammelten Zeilen zu einer Frage zusammenfassen)
                question_text = " ".join(question_lines).strip()
                
                # Wenn wir eine gültige Kategorie und nicht-leere Frage haben, abspeichern
                if current_category and question_text:
                    questions.append({
                        "id": question_id,
                        "question": question_text,
                        "answer": answer,
                        "category": current_category
                    })
                    question_id += 1

                # Puffer leeren für die nächste Frage
                question_lines = []

            # 3) Alles andere wird als Teil der Frage gespeichert
            else:
                # Falls wir gerade eine Kategorie haben und die Zeile nicht leer ist,
                # hängen wir sie an die aktuelle Frage an.
                if current_category and line:
                    question_lines.append(line)

    return questions, categories

# -------------------------------------
# QuizGame-Klasse
# -------------------------------------
class QuizGame:
    def __init__(self):
        self.groups = []
        self.current_group_index = 0
        self.current_question = None
        self.current_category = None
        self.scores = {}
        self.questions, self.categories = load_questions("Quizfragen.txt")
        self.used_questions = []
        self.attempted_by_other_groups = False
        # Neues Attribut für Buzzerrunde: speichert, welche Gruppe bereits geantwortet hat.
        self.buzz_answers = {}

    def start_game(self, num_groups):
        self.groups = [f"Gruppe {i + 1}" for i in range(num_groups)]
        self.scores = {group: 0 for group in self.groups}
        self.current_group_index = 0
        # Falls keine Kategorien vorhanden sind, bleibt current_category None
        if self.categories:
            self.current_category = self.categories[0]
        self.attempted_by_other_groups = False
        self.buzz_answers = {}

    def pick_question(self):
        # Falls keine Kategorie vorhanden ist, gibt es keine Fragen
        if not self.current_category:
            return None

        # Fragen filtern, die noch nicht benutzt wurden und zur aktuellen Kategorie passen
        available_questions = [
            q for q in self.questions
            if q not in self.used_questions and q['category'] == self.current_category
        ]
        if available_questions:
            self.current_question = random.choice(available_questions)
            self.used_questions.append(self.current_question)
            # Falls es sich um eine Buzzerrunde handelt, leere die Buzz-Antworten
            if self.current_category == "Buzzerrunde":
                self.buzz_answers = {}
            return self.current_question
        return None

    def answer_buzz(self, group, correct):
        # Punktevergabe: +6 für richtig, -6 für falsch
        if correct:
            self.scores[group] += 6
        else:
            self.scores[group] -= 6
        self.buzz_answers[group] = correct

    def next_turn(self):
        # Standard-Logik: Runde beenden und ggf. Kategorie wechseln
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        if self.current_group_index == 0 and self.categories:
            current_category_index = self.categories.index(self.current_category)
            self.current_category = self.categories[(current_category_index + 1) % len(self.categories)]
        self.attempted_by_other_groups = False
        # Bei Buzzerrunde auch die gespeicherten Antworten zurücksetzen
        self.buzz_answers = {}
        if 'selected_dice' in st.session_state:
            del st.session_state['selected_dice']

# -------------------------------------
# Callback-Funktionen
# -------------------------------------
def start_game_callback():
    num_groups = st.session_state.get('num_groups', 1)
    quiz_game.start_game(num_groups)
    st.session_state.game_started = True

def pick_question_callback():
    question = quiz_game.pick_question()
    if question:
        st.session_state.current_question = question
        st.session_state.current_question_id = question['id']  # Frage-ID speichern
        st.session_state.show_answer = False
        st.session_state.answered_correctly = None
    else:
        st.session_state.no_more_questions = True

def answer_correct_callback():
    st.session_state.show_answer = True
    st.session_state.answered_correctly = True
    points = st.session_state.get('selected_points', 1)
    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] += points

def answer_wrong_callback():
    st.session_state.show_answer = True
    st.session_state.answered_correctly = False
    points = st.session_state.get('selected_points', 1)
    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] -= points

def next_round_callback():
    quiz_game.next_turn()
    st.session_state.pop('current_question', None)
    st.session_state.pop('current_question_id', None)
    st.session_state.show_answer = False
    st.session_state.answered_correctly = None

def other_group_correct_callback(group):
    quiz_game.scores[group] += 2

def other_group_wrong_callback(group):
    quiz_game.scores[group] -= 1

# Neuer Callback für Buzzerrunde-Antworten
def buzz_answer_callback(group, correct):
    # Überprüfen, ob diese Gruppe bereits geantwortet hat
    if group in quiz_game.buzz_answers:
        return  # Falls ja, keine weitere Verarbeitung
    quiz_game.answer_buzz(group, correct)
    # Kein explizites st.experimental_rerun() – der Callback führt ohnehin zu einem Neulauf

# -------------------------------------
# Streamlit-App
# -------------------------------------
st.title("Quiz Spiel")

# Sidebar: Frage und Antwort (inkl. IDs) immer anzeigen
with st.sidebar:
    st.header("Aktuelle Frage & Antwort")
    if 'current_question' in st.session_state:
        q = st.session_state.current_question
        st.write(f"**Frage (ID {q['id']}):** {q['question']}")
        st.write(f"**Antwort (ID {q['id']}):** {q['answer']}")
        # Test, ob Frage-ID und Antwort-ID übereinstimmen
        if q['id'] == q['id']:
            st.write("Die Frage-ID und Antwort-ID stimmen überein.")
    else:
        st.write("Zurzeit keine aktive Frage.")

# QuizGame initialisieren
if 'quiz_game' not in st.session_state:
    st.session_state.quiz_game = QuizGame()
quiz_game = st.session_state.quiz_game

# Spielstart
if 'game_started' not in st.session_state:
    st.session_state.num_groups = st.number_input("Anzahl der Gruppen (1-6):", min_value=1, max_value=6, value=1)
    st.button("Spiel starten", on_click=start_game_callback)
else:
    st.write(f"Aktuelle Gruppe: {quiz_game.groups[quiz_game.current_group_index]}")
    st.write(f"Aktuelle Kategorie: {quiz_game.current_category}")

    # Wenn noch keine Frage gezogen wurde
    if 'current_question' not in st.session_state:
        st.session_state.selected_dice = st.number_input("Geworfene Zahl (1-6) eingeben:", min_value=1, max_value=6, value=1)
        st.session_state.selected_points = st.number_input("Punkte setzen (1-6):", min_value=1, max_value=6, value=1)
        st.button("Frage auswählen", on_click=pick_question_callback)
    else:
        q = st.session_state.current_question
        st.write(f"**Frage (ID {q['id']}):** {q['question']}")

        # Sonderfall: Buzzerrunde
        if quiz_game.current_category == "Buzzerrunde":
            st.write("**Buzzerrunde:** Alle Gruppen beantworten diese Frage!")
            # Für jede Gruppe, falls noch nicht geantwortet, werden Antwort-Buttons angezeigt
            for group in quiz_game.groups:
                if group not in quiz_game.buzz_answers:
                    col_r, col_w = st.columns(2)
                    with col_r:
                        st.button(f"{group} - Richtig", key=f"{group}_r", on_click=buzz_answer_callback, args=(group, True))
                    with col_w:
                        st.button(f"{group} - Falsch", key=f"{group}_w", on_click=buzz_answer_callback, args=(group, False))
                else:
                    antwort = "richtig" if quiz_game.buzz_answers[group] else "falsch"
                    st.write(f"{group} hat bereits {antwort} geantwortet.")

            # Sobald alle Gruppen geantwortet haben, wird die Antwort angezeigt und "Nächste Runde" freigegeben.
            if len(quiz_game.buzz_answers) == len(quiz_game.groups):
                st.write(f"**Antwort:** {q['answer']} (ID {q['id']})")
                st.button("Nächste Runde", on_click=next_round_callback)
        else:
            # Standard-Logik für alle anderen Kategorien:
            st.write(f"(Antwort (ID {q['id']}))")
            if st.session_state.get('answered_correctly') is None:
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Richtig", key="correct", on_click=answer_correct_callback)
                with col2:
                    st.button("Falsch", key="wrong", on_click=answer_wrong_callback)

            if st.session_state.get('show_answer', False):
                st.write(f"**Antwort:** {q['answer']} (ID {q['id']})")
                if st.session_state.get('answered_correctly') == False:
                    st.write("Andere Gruppen können jetzt antworten:")
                    for group in quiz_game.groups:
                        if group != quiz_game.groups[quiz_game.current_group_index]:
                            col_r, col_f = st.columns(2)
                            with col_r:
                                st.button(f"{group} (Richtig)", on_click=lambda grp=group: other_group_correct_callback(grp))
                            with col_f:
                                st.button(f"{group} (Falsch)", on_click=lambda grp=group: other_group_wrong_callback(grp))
                st.button("Nächste Runde", on_click=next_round_callback)

    # Punktestände anzeigen
    st.write("**Punktestände:**")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")

# Wenn keine Fragen mehr vorhanden
if st.session_state.get('no_more_questions'):
    st.write("Das Spiel ist zu Ende! Alle Fragen wurden gestellt.")
