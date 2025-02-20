import streamlit as st
import random

# Quizfragen aus der Datei laden
def load_questions(filename):
    questions = []
    categories = []
    current_category = None
    
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("Kategorie:"):
            current_category = line.replace("Kategorie: ", "").strip()
            categories.append(current_category)
        elif current_category and line:  # Wenn eine Kategorie gesetzt ist und die Zeile nicht leer ist
            question = line
            # Sicherstellen, dass die nächste Zeile existiert, bevor wir darauf zugreifen
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("Antwort:"):
                answer = lines[i + 1].strip().replace("Antwort: ", "")
                questions.append((question, answer, current_category))
    
    return questions, categories

# Hauptfunktion für das Quizspiel
def quiz_game():
    st.title("Quizspiel")
    
    questions, categories = load_questions("Alle_150_Quizfragen.txt")
    used_questions = []
    
    if 'groups' not in st.session_state:
        st.session_state.groups = []
    if 'current_group_index' not in st.session_state:
        st.session_state.current_group_index = 0
    if 'current_category_index' not in st.session_state:
        st.session_state.current_category_index = 0
    if 'selected_dice' not in st.session_state:
        st.session_state.selected_dice = None
    if 'selected_points' not in st.session_state:
        st.session_state.selected_points = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None

    # Eingabe der Gruppenanzahl
    num_groups = st.number_input("Anzahl der Gruppen eingeben:", min_value=1, max_value=6, value=1)
    
    if st.button("Start"):
        st.session_state.groups = [{"name": f"Gruppe {i+1}", "points": 0} for i in range(num_groups)]
        st.session_state.current_group_index = 0
        st.session_state.current_category_index = 0
        st.session_state.selected_dice = None
        st.session_state.selected_points = None
        st.session_state.used_questions = []
        st.session_state.current_question = None

    # Anzeige der aktuellen Gruppe und Kategorie
    if st.session_state.groups:
        st.write(f"Aktuelle Gruppe: {st.session_state.groups[st.session_state.current_group_index]['name']}")
        st.write(f"Aktuelle Kategorie: {categories[st.session_state.current_category_index]}")

        # Würfel- und Punkteauswahl
        st.subheader("Würfel- und Punkteauswahl")
        selected_dice = st.radio("Gewürfelte Zahl wählen:", [1, 2, 3, 4, 5, 6], index=0)
        selected_points = st.radio("Punkte setzen:", [1, 2, 3, 4, 5, 6], index=0)

        if st.button("Frage stellen"):
            st.session_state.selected_dice = selected_dice
            st.session_state.selected_points = selected_points
            pick_question(questions, categories, used_questions)

        if st.session_state.current_question:
            st.write(f"Frage: {st.session_state.current_question[0]}")
            if st.button("Richtig"):
                st.session_state.groups[st.session_state.current_group_index]["points"] += st.session_state.selected_points
                next_turn()
            if st.button("Falsch"):
                select_attempt_group()
            if st.button("Keine weitere Gruppe"):
                no_attempt()

        st.write("Punkte:")
        for group in st.session_state.groups:
            st.write(f"{group['name']}: {group['points']} Punkte")

def pick_question(questions, categories, used_questions):
    filtered_questions = [q for q in questions if q[2] == categories[st.session_state.current_category_index]]
    available_questions = [q for q in filtered_questions if q not in used_questions]

    if not available_questions:
        st.warning("Es gibt keine Fragen mehr in dieser Kategorie.")
        next_turn()
        return

    st.session_state.current_question = random.choice(available_questions)
    used_questions.append(st.session_state.current_question)

def next_turn():
    st.session_state.current_group_index = (st.session_state.current_group_index + 1) % len(st.session_state.groups)
    if st.session_state.current_group_index == 0:
        st.session_state.current_category_index = (st.session_state.current_category_index + 1) % len(categories)

    st.session_state.current_question = None
    st.session_state.selected_dice = None
    st.session_state.selected_points = None

def select_attempt_group():
    # Hier könnte eine Logik für die Auswahl einer anderen Gruppe implementiert werden
    st.write("Hier könnte eine Logik für die Auswahl einer anderen Gruppe implementiert werden.")

def no_attempt():
    # Hier könnte eine Logik für den Fall implementiert werden, dass keine Gruppe antwortet
    st.write("Hier könnte eine Logik für den Fall implementiert werden, dass keine Gruppe antwortet.")

if __name__ == "__main__":
    quiz_game()
