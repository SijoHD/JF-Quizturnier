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
                current_category = line.split(":")[1].strip()
                categories.append(current_category)
            elif line.startswith("Wie") or line.startswith("Was") or line.startswith("Welcher") or line.startswith("Wofür"):
                question = line
            elif line.startswith("Antwort:") and current_category:
                answer = line.split("Antwort:")[1].strip()
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
        available_questions = [q for q in self.questions if q not in self.used_questions and q['category'] == self.current_category]
        if available_questions:
            self.current_question = random.choice(available_questions)
            self.used_questions.append(self.current_question)
            return self.current_question
        return None

    def next_turn(self):
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        if self.current_group_index == 0:
            # Wechsel zur nächsten Kategorie
            current_category_index = self.categories.index(self.current_category)
            self.current_category = self.categories[(current_category_index + 1) % len(self.categories)]
        self.attempted_by_other_groups = False

# Streamlit UI
st.title("Quiz Spiel")

# Spielinitialisierung
quiz_game = QuizGame()

# Anzahl der Gruppen eingeben
num_groups = st.number_input("Anzahl der Gruppen (1-6):", min_value=1, max_value=6, value=1)

if st.button("Spiel starten"):
    quiz_game.start_game(num_groups)
    st.session_state['quiz_game'] = quiz_game
    st.session_state['current_question'] = None
    st.session_state['selected_dice'] = None
    st.session_state['selected_points'] = None

# Spielverlauf
if 'quiz_game' in st.session_state:
    quiz_game = st.session_state['quiz_game']
    st.write(f"Aktuelle Gruppe: {quiz_game.groups[quiz_game.current_group_index]}")
    st.write(f"Aktuelle Kategorie: {quiz_game.current_category}")

    # Würfeln
    if st.button("Würfeln"):
        st.session_state['selected_dice'] = random.randint(1, 6)
        st.write(f"Geworfene Zahl: {st.session_state['selected_dice']}")

    # Punkte setzen
    points = st.number_input("Punkte setzen (1-6):", min_value=1, max_value=6, value=1)
    st.session_state['selected_points'] = points

    # Frage auswählen
    if st.button("Frage auswählen"):
        question = quiz_game.pick_question()
        if question:
            st.session_state['current_question'] = question
            st.write(f"Frage: {question['question']}")
            st.session_state['show_answer'] = False  # Antwort zunächst nicht anzeigen
            st.session_state['answered_correctly'] = None  # Reset der Antwortstatus
            st.session_state['other_group_answered'] = False  # Reset für andere Gruppen
        else:
            st.write("Keine Fragen mehr verfügbar.")

    # Antwortmöglichkeiten
    if st.session_state['current_question']:
        # Buttons für Richtig und Falsch für die aktuelle Gruppe
        if not quiz_game.attempted_by_other_groups:
            if st.button("Richtig"):
                st.session_state['show_answer'] = True
                st.session_state['answered_correctly'] = True
                st.write("Richtige Antwort!")
                quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] += st.session_state['selected_points']
                quiz_game.next_turn()
                st.session_state['current_question'] = None
            if st.button("Falsch"):
                st.session_state['show_answer'] = True
                st.session_state['answered_correctly'] = False
                st.write("Falsche Antwort!")
                quiz_game.attempted_by_other_groups = True  # Andere Gruppen dürfen jetzt antworten

        # Anzeige der Antwort
        if st.session_state.get('show_answer', False):
            st.write(f"Antwort: {st.session_state['current_question']['answer']}")
            # Möglichkeit für andere Gruppen, zu antworten
            for i, group in enumerate(quiz_game.groups):
                if i != quiz_game.current_group_index and not st.session_state['other_group_answered']:
                    if st.button(f"{group} antworten"):
                        st.session_state['other_group_answered'] = True  # Markiere, dass eine andere Gruppe geantwortet hat
                        # Auswahl, ob die andere Gruppe richtig oder falsch geantwortet hat
                        if st.button("Richtig", key=f"correct_{i}"):
                            st.write(f"{group} hat richtig geantwortet!")
                            quiz_game.scores[group] += 2
                        elif st.button("Falsch", key=f"wrong_{i}"):
                            st.write(f"{group} hat falsch geantwortet!")
                            quiz_game.scores[group] -= 2
            quiz_game.next_turn()
            st.session_state['current_question'] = None

    # Punktestände anzeigen
    st.write("Punktestände:")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")

# Spielende
if len(quiz_game.used_questions) == len(quiz_game.questions):
    st.write("Das Spiel ist zu Ende! Alle Fragen wurden gestellt.")
