import streamlit as st
import random

# CSS für einen festen Footer in der Sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] .fixed-footer {
        position: fixed;
        bottom: 0;
        width: 230px;  /* Passe die Breite nach Bedarf an */
        background-color: #f0f2f6;
        padding: 10px;
        border-top: 1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
                current_category = line.split(":", 1)[1].strip()
                if current_category not in categories:
                    categories.append(current_category)

            # 2) Antwort-Zeile
            elif line.startswith("Antwort:"):
                answer = line.split("Antwort:", 1)[1].strip()
                question_text = " ".join(question_lines).strip()
                if current_category and question_text:
                    questions.append({
                        "id": question_id,
                        "question": question_text,
                        "answer": answer,
                        "category": current_category
                    })
                    question_id += 1
                question_lines = []

            # 3) Zeile als Teil der Frage
            else:
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
        # Für Buzzerrunde: speichert alle Buzzes pro Gruppe als Liste
        self.buzz_answers = {}

    def start_game(self, num_groups):
        self.groups = [f"Gruppe {i + 1}" for i in range(num_groups)]
        self.scores = {group: 0 for group in self.groups}
        self.current_group_index = 0
        if self.categories:
            self.current_category = self.categories[0]
        self.attempted_by_other_groups = False
        self.buzz_answers = {}

    def pick_question(self):
        if not self.current_category:
            return None
        available_questions = [
            q for q in self.questions
            if q not in self.used_questions and q['category'] == self.current_category
        ]
        if available_questions:
            self.current_question = random.choice(available_questions)
            self.used_questions.append(self.current_question)
            if self.current_category == "Buzzerrunde":
                self.buzz_answers = {}  # Alle Buzzes für diese Frage zurücksetzen
            return self.current_question
        return None

    def answer_buzz(self, group, correct):
        # Punktevergabe: +6 für richtig, -6 für falsch
        if correct:
            self.scores[group] += 6
        else:
            self.scores[group] -= 6
        # Jeder Buzz wird als neue Antwort hinzugefügt
        if group in self.buzz_answers:
            self.buzz_answers[group].append(correct)
        else:
            self.buzz_answers[group] = [correct]

    def next_turn(self):
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        if self.current_group_index == 0 and self.categories:
            current_category_index = self.categories.index(self.current_category)
            self.current_category = self.categories[(current_category_index + 1) % len(self.categories)]
        self.attempted_by_other_groups = False
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
        st.session_state.current_question_id = question['id']
        st.session_state.show_answer = False
        st.session_state.answered_correctly = None
        st.session_state.buzzed_group = ""
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
    st.session_state.buzzed_group = ""

def other_group_correct_callback(group):
    quiz_game.scores[group] += 2

def other_group_wrong_callback(group):
    quiz_game.scores[group] -= 1

def buzz_answer_callback(group, correct):
    # Hier erfolgt KEINE Prüfung, ob die Gruppe schon geantwortet hat – jeder Buzz zählt.
    quiz_game.answer_buzz(group, correct)
    st.session_state.buzzed_group = group

# Skip-Funktion in der Buzzerrunde: wechselt zur nächsten Frage,
# wenn entweder keine Gruppe ausgewählt oder keine Antwort registriert wurde.
def skip_buzz_question_callback():
    if not st.session_state.get("buzzed_group", "") or not quiz_game.buzz_answers:
        next_round_callback()

# Skip-Funktion im normalen Spielmodus
def skip_normal_question_callback():
    next_round_callback()

# -------------------------------------
# Streamlit-App
# -------------------------------------
st.title("Quiz Spiel")

# Sidebar: Oben erscheint weiterhin der statische Bereich "Aktuelle Frage & Antwort"
with st.sidebar:
    st.header("Aktuelle Frage & Antwort")
    if 'current_question' in st.session_state:
        q = st.session_state.current_question
        st.write(f"**Frage (ID {q['id']}):** {q['question']}")
        st.write(f"**Antwort (ID {q['id']}):** {q['answer']}")
        st.write("Die Frage-ID und Antwort-ID stimmen überein.")
    else:
        st.write("Zurzeit keine aktive Frage.")

# Hauptbereich bzw. Spielsteuerung
if 'quiz_game' not in st.session_state:
    st.session_state.quiz_game = QuizGame()
quiz_game = st.session_state.quiz_game

if 'game_started' not in st.session_state:
    st.session_state.num_groups = st.number_input("Anzahl der Gruppen (1-6):", min_value=1, max_value=6, value=1)
    st.button("Spiel starten", on_click=start_game_callback)
else:
    st.write(f"Aktuelle Gruppe: {quiz_game.groups[quiz_game.current_group_index]}")
    st.write(f"Aktuelle Kategorie: {quiz_game.current_category}")

    if 'current_question' not in st.session_state:
        st.session_state.selected_dice = st.number_input("Geworfene Zahl (1-6) eingeben:", min_value=1, max_value=6, value=1)
        st.session_state.selected_points = st.number_input("Punkte setzen (1-6):", min_value=1, max_value=6, value=1)
        st.button("Frage auswählen", on_click=pick_question_callback)
    else:
        q = st.session_state.current_question
        st.write(f"**Frage (ID {q['id']}):** {q['question']}")

        # Buzzerrunde: Es erfolgt extern (über Dropdown) die Auswahl der buzzenden Gruppe.
        if quiz_game.current_category == "Buzzerrunde":
            st.write("**Buzzerrunde:** Wähle die Gruppe, die als Erste buzzert hat.")
            if "buzzed_group" not in st.session_state:
                st.session_state.buzzed_group = ""
            selected_group = st.selectbox("Welche Gruppe hat gebuzzert?", [""] + quiz_game.groups, key="buzzed_group")
            if selected_group:
                st.write(f"{selected_group} hat gebuzzert. Bitte wähle, ob die Antwort richtig oder falsch war.")
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Richtig", key=f"{selected_group}_r", on_click=buzz_answer_callback, args=(selected_group, True))
                with col2:
                    st.button("Falsch", key=f"{selected_group}_f", on_click=buzz_answer_callback, args=(selected_group, False))
            else:
                st.write("Noch keine Gruppe ausgewählt.")

            if not quiz_game.buzz_answers:
                st.button("Keine Antwort? Zur nächsten Frage", on_click=skip_buzz_question_callback)
            else:
                st.write(f"**Antwort:** {q['answer']} (ID {q['id']})")
                st.button("Nächste Runde", on_click=next_round_callback)

        # Normaler Spielmodus
        else:
            st.write(f"(Antwort (ID {q['id']}))")
            if st.session_state.get('answered_correctly') is None:
                col1, col2, col_skip = st.columns(3)
                with col1:
                    st.button("Richtig", key="correct", on_click=answer_correct_callback)
                with col2:
                    st.button("Falsch", key="wrong", on_click=answer_wrong_callback)
                with col_skip:
                    st.button("Keine Antwort? Überspringen", on_click=skip_normal_question_callback)
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

    st.write("**Punktestände:**")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")

if st.session_state.get('no_more_questions'):
    st.write("Das Spiel ist zu Ende! Alle Fragen wurden gestellt.")

# Fester Footer in der Sidebar: Rangliste und aktuelle Frage
with st.sidebar:
    st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
    st.markdown("### Aktuelle Rangliste")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")
    if 'current_question' in st.session_state:
        q = st.session_state.current_question
        st.markdown("### Aktuelle Frage")
        st.write(f"**Frage (ID {q['id']}):** {q['question']}")
    st.markdown('</div>', unsafe_allow_html=True)
