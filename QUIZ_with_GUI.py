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
            elif line.startswith(("Wie", "Was", "Welcher", "Wofür")):
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
        """Zur nächsten Gruppe wechseln und ggf. Kategorie wechseln."""
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        if self.current_group_index == 0:
            current_category_index = self.categories.index(self.current_category)
            self.current_category = self.categories[(current_category_index + 1) % len(self.categories)]
        self.attempted_by_other_groups = False


# --------------------------------
# Streamlit UI
# --------------------------------
st.title("Quiz Spiel")

# Spielinitialisierung
if 'quiz_game' not in st.session_state:
    st.session_state['quiz_game'] = QuizGame()
quiz_game = st.session_state['quiz_game']

# Anzahl der Gruppen eingeben
num_groups = st.number_input(
    "Anzahl der Gruppen (1-6):",
    min_value=1, max_value=6, value=1,
    disabled='current_question' in st.session_state
)

if st.button("Spiel starten", disabled='current_question' in st.session_state):
    quiz_game.start_game(num_groups)
    st.session_state.clear()
    st.session_state['quiz_game'] = quiz_game

# Spielverlauf
if quiz_game.groups:
    st.write(f"Aktuelle Gruppe: {quiz_game.groups[quiz_game.current_group_index]}")
    st.write(f"Aktuelle Kategorie: {quiz_game.current_category}")

    # Würfeln
    # --> Button ist nur gesperrt, wenn gerade eine Frage offen ist,
    #     damit nicht während der Frage neu gewürfelt wird.
    if st.button("Würfeln", disabled='current_question' in st.session_state):
        st.session_state['selected_dice'] = random.randint(1, 6)
    # Zeige geworfene Zahl, falls vorhanden
    if 'selected_dice' in st.session_state:
        st.write(f"Geworfene Zahl: {st.session_state['selected_dice']}")

    # Punkte setzen
    points = st.number_input(
        "Punkte setzen (1-6):",
        min_value=1, max_value=6, value=1,
        disabled='current_question' in st.session_state
    )
    st.session_state['selected_points'] = points

    # Frage auswählen
    if st.button("Frage auswählen", disabled='current_question' in st.session_state):
        question = quiz_game.pick_question()
        if question:
            st.session_state['current_question'] = question
            st.session_state['show_answer'] = False
            st.session_state['answered_correctly'] = None
            st.session_state['other_group_answered'] = False
        else:
            st.write("Keine Fragen mehr verfügbar.")

    # Wenn eine aktuelle Frage existiert
    if 'current_question' in st.session_state:
        question = st.session_state['current_question']
        st.write(f"Frage: {question['question']}")

        # Buttons für Richtig/Falsch nur, wenn die aktuelle Gruppe noch nicht geantwortet hat
        if not quiz_game.attempted_by_other_groups:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Richtig", key="correct", disabled=st.session_state.get('answered_correctly') is not None):
                    st.session_state['show_answer'] = True
                    st.session_state['answered_correctly'] = True
                    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] += st.session_state['selected_points']
                    # Da richtig beantwortet: direkt nächste Gruppe
                    quiz_game.next_turn()
                    # Beim Gruppenwechsel: alten Würfelwurf entfernen
                    if 'selected_dice' in st.session_state:
                        del st.session_state['selected_dice']
                    del st.session_state['current_question']
            with col2:
                if st.button("Falsch", key="wrong", disabled=st.session_state.get('answered_correctly') is not None):
                    st.session_state['show_answer'] = True
                    st.session_state['answered_correctly'] = False
                    # Andere Gruppen dürfen antworten
                    quiz_game.attempted_by_other_groups = True

        # Anzeige der Antwort und ggf. andere Gruppen dürfen antworten
        if st.session_state.get('show_answer', False):
            st.write(f"**Antwort:** {question['answer']}")
            
            # Nur wenn die aktuelle Gruppe falsch geantwortet hat, dürfen andere Gruppen ran
            if st.session_state.get('answered_correctly') == False:
                if not st.session_state['other_group_answered']:
                    for i, group in enumerate(quiz_game.groups):
                        if i != quiz_game.current_group_index:
                            if st.button(f"{group} antworten", key=f"group_{i}", disabled=st.session_state['other_group_answered']):
                                st.session_state['other_group_answered'] = True
                                col3, col4 = st.columns(2)
                                with col3:
                                    if st.button("Richtig", key=f"correct_{i}"):
                                        quiz_game.scores[group] += 2
                                with col4:
                                    if st.button("Falsch", key=f"wrong_{i}"):
                                        quiz_game.scores[group] -= 2

                # Nachdem andere Gruppen geantwortet haben (oder gar nicht), geht's zur nächsten Gruppe
                quiz_game.next_turn()
                # Beim Gruppenwechsel: alten Würfelwurf entfernen
                if 'selected_dice' in st.session_state:
                    del st.session_state['selected_dice']
                if 'current_question' in st.session_state:
                    del st.session_state['current_question']

    # Punktestände
    st.write("Punktestände:")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")

# Wenn alle Fragen aufgebraucht sind
if len(quiz_game.used_questions) == len(quiz_game.questions) and quiz_game.questions:
    st.write("Das Spiel ist zu Ende! Alle Fragen wurden gestellt.")
