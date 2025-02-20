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
        elif current_category and line:
            question = line
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("Antwort:"):
                answer = lines[i + 1].strip().replace("Antwort: ", "")
                questions.append((question, answer, current_category))
    
    return questions, categories

# Initialisiere den Quiz-Status
if "questions" not in st.session_state:
    st.session_state.questions, st.session_state.categories = load_questions("Alle_150_Quizfragen.txt")
    st.session_state.used_questions = []
    st.session_state.groups = []
    st.session_state.current_group_index = 0
    st.session_state.current_category_index = 0
    st.session_state.selected_dice = None
    st.session_state.selected_points = None
    st.session_state.current_question = None
    st.session_state.selected_attempt_group = None
    # Dictionary zur Verfolgung der beantworteten Fragen pro Gruppe und Kategorie
    st.session_state.answered_questions = {group['name']: {category: False for category in st.session_state.categories} for group in st.session_state.groups}

st.title("Quizspiel")

# Eingabe für die Anzahl der Gruppen
num_groups = st.number_input("Anzahl der Gruppen eingeben:", min_value=1, max_value=6, step=1)
if st.button("Start"):
    st.session_state.groups = [{"name": f"Gruppe {i+1}", "points": 0} for i in range(num_groups)]
    st.session_state.answered_questions = {group['name']: {category: False for category in st.session_state.categories} for group in st.session_state.groups}
    st.session_state.current_group_index = 0
    st.session_state.current_category_index = 0

if st.session_state.groups:
    st.write(f"**Aktuelle Gruppe:** {st.session_state.groups[st.session_state.current_group_index]['name']}")
    st.write(f"**Aktuelle Kategorie:** {st.session_state.categories[st.session_state.current_category_index]}")

    # Würfel- und Punkteauswahl per Buttons
    st.write("**Gewürfelte Zahl wählen:**")
    cols = st.columns(6)
    for i in range(1, 7):
        if cols[i - 1].button(str(i)):
            st.session_state.selected_dice = i
            
    st.write("**Punkte setzen:**")
    cols = st.columns(6)
    for i in range(1, 7):
        if cols[i - 1].button(f"{i} Punkte"):
            st.session_state.selected_points = i
            
    # Automatische Frageziehung, wenn beide Werte gesetzt sind
    if st.session_state.selected_dice and st.session_state.selected_points:
        filtered_questions = [q for q in st.session_state.questions if q[2] == st.session_state.categories[st.session_state.current_category_index]]
        available_questions = [q for q in filtered_questions if q not in st.session_state.used_questions and not st.session_state.answered_questions[st.session_state.groups[st.session_state.current_group_index]['name']][q[2]]]
        
        if available_questions:
            st.session_state.current_question = random.choice(available_questions)
            st.session_state.used_questions.append(st.session_state.current_question)
        else:
            st.warning("Keine Fragen mehr in dieser Kategorie für diese Gruppe.")

    # Frage anzeigen, wenn die aktuelle Gruppe ihre Punkte und Würfelzahl ausgewählt hat
    if st.session_state.current_question:
        st.write(f"**Frage:** {st.session_state.current_question[0]}")
        if st.button("Antwort anzeigen"):
            st.write(f"**Antwort:** {st.session_state.current_question[1]}")

        cols = st.columns(2)
        if cols[0].button("Richtig"):
            st.session_state.groups[st.session_state.current_group_index]["points"] += st.session_state.selected_points
            # Markiere die Kategorie als beantwortet für die aktuelle Gruppe
            st.session_state.answered_questions[st.session_state.groups[st.session_state.current_group_index]['name']][st.session_state.current_question[2]] = True
            st.session_state.current_question = None
            
            # Nächste Gruppe ist an der Reihe
            st.session_state.current_group_index = (st.session_state.current_group_index + 1) % len(st.session_state.groups)
            if st.session_state.current_group_index == 0:
                st.session_state.current_category_index = (st.session_state.current_category_index + 1) % len(st.session_state.categories)
            
            # Zurücksetzen der Würfel- und Punkteauswahl
            st.session_state.selected_dice = None
            st.session_state.selected_points = None
        
        if cols[1].button("Falsch"):
            attempt_groups = [g['name'] for g in st.session_state.groups if g['name'] != st.session_state.groups[st.session_state.current_group_index]['name']]
            for group in attempt_groups:
                if st.button(group):
                    st.session_state.selected_attempt_group = group
                    
            if st.session_state.selected_attempt_group:
                cols = st.columns(2)
                if cols[0].button("Ja"):
                    st.session_state.groups[[g["name"] for g in st.session_state.groups].index(st.session_state.selected_attempt_group)]["points"] += 2
                if cols[1].button("Nein"):
                    st.session_state.groups[[g["name"] for g in st.session_state.groups].index(st.session_state.selected_attempt_group)]["points"] -= 2

            # Zurücksetzen der Würfel- und Punkteauswahl
            st.session_state.selected_dice = None
            st.session_state.selected_points = None

    st.write("**Punkteübersicht:**")
    for group in st.session_state.groups:
        st.write(f"{group['name']}: {group['points']} Punkte")
