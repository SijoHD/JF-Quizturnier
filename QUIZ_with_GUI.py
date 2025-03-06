
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
        """
        Nächste Gruppe ist dran, ggf. Kategorie-Wechsel und Würfel-Ergebnis löschen.
        """
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        if self.current_group_index == 0:
            current_category_index = self.categories.index(self.current_category)
            self.current_category = self.categories[(current_category_index + 1) % len(self.categories)]
        self.attempted_by_other_groups = False

        # Entferne den Würfelwert, damit jede Gruppe neu einen Wert eingeben kann
        if 'selected_dice' in st.session_state:
            del st.session_state['selected_dice']


# -----------------------------
# Streamlit App
# -----------------------------
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
    # Session-Status zurücksetzen (Achtung: dabei wird auch quiz_game entfernt)
    st.session_state.clear()
    # quiz_game erneut speichern
    st.session_state['quiz_game'] = quiz_game

# Wenn das Spiel läuft (Gruppen existieren)
if quiz_game.groups:
    st.write(f"Aktuelle Gruppe: {quiz_game.groups[quiz_game.current_group_index]}")
    st.write(f"Aktuelle Kategorie: {quiz_game.current_category}")

    # Geworfene Zahl manuell eingeben (statt random Würfeln)
    if 'current_question' not in st.session_state:
        # Nur solange keine Frage läuft, darf die Gruppe ihren Würfelwert neu setzen
        st.session_state['selected_dice'] = st.number_input(
            "Geworfene Zahl (1-6) eingeben:",
            min_value=1, max_value=6, value=1
        )
        st.write(f"Geworfene Zahl: {st.session_state['selected_dice']}")
    else:
        # Wenn eine Frage läuft, zeige an, was bereits 'gewürfelt' wurde
        if 'selected_dice' in st.session_state:
            st.write(f"Geworfene Zahl: {st.session_state['selected_dice']}")
        else:
            st.write("Noch kein Wert für diesen Zug gesetzt.")

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
        else:
            st.write("Keine Fragen mehr verfügbar.")

    # Falls eine aktuelle Frage existiert
    if 'current_question' in st.session_state:
        question = st.session_state['current_question']
        st.write(f"**Frage:** {question['question']}")

        # Buttons für Richtig/Falsch für die aktuelle Gruppe
        if st.session_state.get('answered_correctly') is None:
            col1, col2 = st.columns(2)
            with col1:
                # Richtig
                if st.button("Richtig", key="correct"):
                    st.session_state['show_answer'] = True
                    st.session_state['answered_correctly'] = True
                    # + gesetzte Punkte
                    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] += st.session_state['selected_points']
                    # Nächste Gruppe, Frage entfernen
                    quiz_game.next_turn()
                    del st.session_state['current_question']
            with col2:
                # Falsch
                if st.button("Falsch", key="wrong"):
                    st.session_state['show_answer'] = True
                    st.session_state['answered_correctly'] = False
                    # - gesetzte Punkte
                    quiz_game.scores[quiz_game.groups[quiz_game.current_group_index]] -= st.session_state['selected_points']

        # Wenn die Antwort angezeigt werden soll
        if st.session_state.get('show_answer', False):
            st.write(f"**Antwort:** {question['answer']}")

            # --- Nur wenn die aktuelle Gruppe falsch geantwortet hat, dürfen andere Gruppen ran ---
            if st.session_state.get('answered_correctly') == False:
                st.write("Andere Gruppen können jetzt antworten:")

                # Für jede andere Gruppe Buttons: (Richtig) +2 / (Falsch) -1
                for i, group in enumerate(quiz_game.groups):
                    if i != quiz_game.current_group_index:
                        col_r, col_f = st.columns(2)
                        with col_r:
                            # Richtig
                            if st.button(f"{group} (Richtig)", key=f"{group}_correct"):
                                quiz_game.scores[group] += 2
                        with col_f:
                            # Falsch
                            if st.button(f"{group} (Falsch)", key=f"{group}_wrong"):
                                quiz_game.scores[group] -= 1

                # Am Ende: „Nächste Runde“-Button
                if st.button("Nächste Runde"):
                    quiz_game.next_turn()
                    del st.session_state['current_question']

    # Punktestände anzeigen
    st.write("**Punktestände:**")
    for group, score in quiz_game.scores.items():
        st.write(f"{group}: {score} Punkte")

# Falls alle Fragen aufgebraucht sind
if len(quiz_game.used_questions) == len(quiz_game.questions) and quiz_game.questions:
    st.write("Das Spiel ist zu Ende! Alle Fragen wurden gestellt.")
