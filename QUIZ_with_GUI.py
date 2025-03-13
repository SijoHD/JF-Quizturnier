import streamlit as st
import random

# (Optional: Entferne oder passe CSS an, falls keine feste Positionierung mehr benötigt wird)
# Falls du kein Fixed-Layout in der Sidebar mehr möchtest, kann der CSS-Block entfallen.
# Falls gewünscht, kann hier weiteres CSS ergänzt werden.

# -------------------------------------
# Funktion zum Laden der Fragen aus der Textdatei
# -------------------------------------
def load_questions(filename):
    questions = []
    categories = []
    current_category = None
    question_id = 1
    question_lines = []  # Puffer für die Zeilen der aktuellen Frage
    buzz_round_counter = 0  # Zähler für Buzzerrunden

    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            
            # 1) Kategorie-Wechsel
            if line.startswith("Kategorie:"):
                new_category = line.split(":", 1)[1].strip()
                # Wenn das erste Wort "Buzzerrunde" lautet, wird ein Zähler hinzugefügt
                if new_category.split()[0].lower() == "buzzerrunde":
                    buzz_round_counter += 1
                    current_category = f"Buzzerrunde {buzz_round_counter}"
                else:
                    current_category = new_category
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
                question_lines = []  # Puffer zurücksetzen

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
            # Falls es sich um eine Buzzerrunde handelt, werden alle Buzzes zurückgesetzt
            if self.current_category.lower().startswith("buzzerrunde"):
                self.buzz_answers = {}
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

        # Buzzerrunde: Auswahl der buzzenden Gruppe (Dropdown)
        if quiz_game.current_category.lower().startswith("buzzerrunde"):
            st.write("**Buzzerrunde:** Wähle die Gruppe, die als Erste buzzert hat.")
            if "buzzed_group" not in st.session_state:
                st.session_state.buzzed_group = ""
            selected_group = st.selectbox("Welche Gruppe hat gebuzzert?", [""] + quiz_game.groups, key="buzzed_group")
            if selected_group:
                st.write(f"{selected_group} hat gebuzzert. Bitte wähle, ob die Antwort richtig oder falsch war.")
            
