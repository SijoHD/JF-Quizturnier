import streamlit as st
import random

# Load questions from a file
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

# Main quiz game function
def quiz_game():
    st.title("Quizspiel")
    
    questions, categories = load_questions("Alle_150_Quizfragen.txt")
    
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
    if 'used_questions' not in st.session_state:
        st.session_state.used_questions = []

    # Input for number of groups
    num_groups = st.number_input("Anzahl der Gruppen eingeben:", min_value=1, max_value=6, value=1)
    
    if st.button("Start"):
        st.session_state.groups = [{"name": f"Gruppe {i+1}", "points": 0} for i in range(num_groups)]
        st.session_state.current_group_index = 0
        st.session_state.current_category_index = 0
        st.session_state.used_questions = []
        st.session_state.current_question = None

    # Display current group and category
    if st.session_state.groups:
        st.write(f"Aktuelle Gruppe: {st.session_state.groups[st.session_state.current_group_index]['name']}")
        st.write(f"Aktuelle Kategorie: {categories[st.session_state.current_category_index]}")

        # Group selection for answering
        selected_group = st.selectbox("Wählen Sie die Gruppe, die antworten möchte:", 
                                       [group['name'] for group in st.session_state.groups])

        # Dice and points selection
        selected_dice = st.radio("Gewürfelte Zahl wählen:", [1, 2, 3, 4, 5, 6], index=0)
        selected_points = st.radio("Punkte setzen:", [1, 2, 3, 4, 5, 6], index=0)

        if st.button("Frage stellen"):
            st.session_state.selected_dice = selected_dice
            st.session_state.selected_points = selected_points
            pick_question(questions, categories)

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

def pick_question(questions, categories):
    filtered_questions = [q for q in questions if q[2] == categories[st.session_state.current_category_index]]
    available_questions = [q for q in filtered_questions
