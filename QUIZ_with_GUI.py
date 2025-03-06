import streamlit as st
import random

# Funktion zum Laden der Fragen aus einer Datei
def load_questions(filename):
    questions = []
    categories = []
    current_category = None

    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith("Kategorie:"):
                current_category = line.split(":", 1)[1].strip()
                categories.append(current_category)
            elif line.startswith(("Wie", "Was", "Welcher", "Wofür")):
                question = line
            elif line.startswith("Antwort:") and current_category:
                answer = line.split("Antwort:", 1)[1].strip()
                questions.append({
                    "question": question,
                    "answer": answer,
                    "category": current_category
                })
    return questions, categories

# QuizGame Klasse
class QuizGame:
    def __init__(self):
        self.groups = []
        self.current_group_index = 0
        self.current_question = None
        self.current_category = None
        self.scores = {}
        self.questions, self.categories = load_questions("Alle_150_Quizfragen.txt")
        self.used_questions = []
        self.attempted_by_other_groups = False

    def start_game(self, num_groups):
        self.groups = [f"Gruppe {i + 1}" for i in range(num_groups)]
        self.scores = {group: 0 for group in self.groups}
        self.current_group_index = 0
        self.current_category = self.categories[0]
        self.attempted_by_other_groups = False

    def pick_question(self):
        available_questions = [
            q for q in self.questions 
            if q not in self.used_questions and q['category'] == self.current_category
        ]
        if available_questions:
            self.current_question = random.choice(available_questions)
            self.used_questions.append(self.current_question)
            return self.current_question
        return None

    def next_turn(self):
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        if self.current_group_index == 0:
            current_category_index = self.categories.index(self.current_category)
            self.current_category = self.categories[(current_category_index + 1) % len(self.categories)]
        self.attempted_by_other_groups = False
        if 'selected_dice' in st.session_state:
            del st.session_state['selected_dice']

# ---------------------------
# Callback-Funktionen
# ---------------------------
def start_game_callback():
    num_groups = st.session_state.get('num_groups', 1)
    quiz_game.start_game(num_groups)
    st.session_state.game_started = True

def pick_question_callback():
    question = quiz_game.pick_question()
    if question:
        st.session_state.current_question = question
        st.session_state.show_answer = False
        st.session_state.answered_correctly = None
    else:
        st.session_state.no_more_questions = True

def answer_correct_callback():
    st.session_state.show_answer = True
    st.session_state.answered_correctly = True
    points = st.session_state.get('selected_points', 1)
    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] += points
    # Hier erfolgt noch kein Übergang zur nächsten Runde

def answer_wrong_callback():
    st.session_state.show_answer = True
    st.session_state.answered_correctly = False
    points = st.session_state.get('selected_points', 1)
    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] -= points
    # Hier erfolgt noch kein Übergang zur nächsten Runde

def next_round_callback():
    quiz_game.next_turn()
    if 'current_question' in st.session_state:
        del st.session_state['current_question']
    st.session_state.show_answer = False
    st.session_state.answered_correctly = None

def other_group_correct_callback(group):
    quiz_game.scores[group] += 2

def other_group_wrong_callback(group):
    quiz_game.scores[group] -= 1

# ---------------------------
# Streamlit App
# ---------------------------
st.title("Quiz Spiel")

# Sidebar: Zeige Frage & Antwort
with st.sidebar:
    st.header("Aktuelle Frage & Antwort")
    if 'current_question' in st.session_state:
        q = st.session_state.current_question
        st.write(f"**Frage:** {q['question']}")
        st.write(f"**Antwort:** {q['answer']}")
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

    # Falls noch keine Frage aktiv ist:
    if 'current_question' not in st.session_state:
        st.session_state.selected_dice = st.number_input("Geworfene Zahl (1-6) eingeben:", min_value=1, max_value=6, value=1)
        st.session_state.selected_points = st.number_input("Punkte setzen (1-6):", min_value=1, max_value=6, value=1)
        st.button("Frage auswählen", on_click=pick_question_callback)
    else:
        q = st.session_state.current_question
        st.write(f"**Frage:** {q['question']}")
        # Antwortbuttons anzeigen, falls noch keine Bewertung erfolgt ist.
        if st.session_state.get('answered_correctly') is None:
            col1, col2 = st.columns(2)
            with col1:
                st.button("Richtig", key="correct", on_click=answer_correct_callback)
            with col2:
                st.button("Falsch", key="wrong", on_click=answer_wrong_callback)
        # Unabhängig von der Bewertung: Sobald show_answer True ist, wird die Antwort direkt unter der Frage angezeigt.
        if st.session_state.get('show_answer', False):
            st.write(f"**Antwort:** {q['answer']}")
            # Falls falsch geantwortet wurde, dürfen andere Gruppen antworten.
            if st.session_state.get('answered_correctly') == False:
                st.write("Andere Gruppen können jetzt antworten:")
                for group in quiz_game.groups:
                    if group != quiz_game.groups[quiz_game.current_group_index]:
                        col_r, col_f = st.columns(2)
                        with col_r:
                            st.button(f"{group} (Richtig)", on_click=lambda grp=group: other_group_correct_callback(grp))
                        with col_f:
                            st.button(f"{group} (Falsch)", on_click=lambda grp=group: other_group_wrong_callback(grp))
            # Button zum Übergang in die nächste Runde – erst wenn die Antwort angezeigt wurde.
            st.button("Nächste Runde", on_click=next_round_callback)

    # Punktestände anzeigen
    st.write("**Punktestände:**")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")

if st.session_state.get('no_more_questions'):
    st.write("Das Spiel ist zu Ende! Alle Fragen wurden gestellt.")

