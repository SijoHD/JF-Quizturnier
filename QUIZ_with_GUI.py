import tkinter as tk
import customtkinter as ctk
import random
from tkinter import messagebox

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

class QuizGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Quizspiel")
        self.root.geometry("1280x720")  # Setze die Fenstergröße auf 1280x720
        ctk.set_appearance_mode("dark")  # Setze den Erscheinungsmodus auf dunkel
        ctk.set_default_color_theme("blue")  # Setze das Farbschema

        self.questions, self.categories = load_questions("Alle_150_Quizfragen.txt")
        self.used_questions = []
        
        self.groups = []
        self.current_group_index = 0
        self.current_question = None
        self.current_category_index = 0  # Index für die aktuelle Kategorie
        
        self.question_window = None  # Attribut für das Frage- und Antwortfenster
        
        self.setup_ui()
    
    def setup_ui(self):
        self.selected_attempt_group = None
        self.selected_dice = None
        self.selected_points = None
        
        # Frame für die Eingabe der Gruppenanzahl
        self.frame_input = ctk.CTkFrame(self.root)
        self.frame_input.pack(pady=30)  # Erhöhtes Padding

        self.label = ctk.CTkLabel(self.frame_input, text="Anzahl der Gruppen eingeben:", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label.pack(side=ctk.LEFT)

        self.entry = ctk.CTkEntry(self.frame_input, font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.entry.pack(side=ctk.LEFT)

        self.button_start = ctk.CTkButton(self.frame_input, text="Start", command=self.start_game, font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.button_start.pack(side=ctk.LEFT)

        # Frame für die Frage und Antwort
        self.frame_question = ctk.CTkFrame(self.root)
        self.frame_question.pack(pady=30)  # Erhöhtes Padding

        self.label_question = ctk.CTkLabel(self.frame_question, text="", wraplength=600, justify="center", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_question.pack()

        self.label_current_group = ctk.CTkLabel(self.root, text="", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_current_group.pack(pady=20)

        self.label_current_category = ctk.CTkLabel(self.root, text="Aktuelle Kategorie: ", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_current_category.pack(pady=20)

        # Frame für die Würfel- und Punkteauswahl
        self.frame_dice_points = ctk.CTkFrame(self.root)
        self.frame_dice_points.pack(side=ctk.LEFT, padx=30, pady=30)  # Erhöhtes Padding

        self.label_dice = ctk.CTkLabel(self.frame_dice_points, text="Gewürfelte Zahl wählen:", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_dice.pack()

        # 3er Block für die Würfelbuttons
        self.dice_frame = ctk.CTkFrame(self.frame_dice_points)
        self.dice_frame.pack(pady=10)

        self.dice_buttons = []
        for i in range(1, 7):
            btn = ctk.CTkButton(self.dice_frame, text=str(i), command=lambda val=i: self.input_dice(val), font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
            btn.grid(row=(i-1)//3, column=(i-1)%3, padx=10, pady=10)  # Erhöhtes Padding
            self.dice_buttons.append(btn)

        self.label_points = ctk.CTkLabel(self.frame_dice_points, text="Punkte setzen:", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_points.pack()

        # 3er Block für die Punktebuttons
        self.point_frame = ctk.CTkFrame(self.frame_dice_points)
        self.point_frame.pack(pady=10)

        self.point_buttons = []
        for i in range(1, 7):
            btn = ctk.CTkButton(self.point_frame, text=str(i), command=lambda val=i: self.set_points(val), font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
            btn.grid(row=(i-1)//3, column=(i-1)%3, padx=10, pady=10)  # Erhöhtes Padding
            self.point_buttons.append(btn)

        # Frame für die Antwortbuttons
        self.frame_buttons = ctk.CTkFrame(self.root)
        self.frame_buttons.pack(pady=30)  # Erhöhtes Padding

        self.button_correct = ctk.CTkButton(self.frame_buttons, text="Richtig", command=self.correct_answer, state=tk.DISABLED, font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.button_correct.pack(side=ctk.LEFT, padx=10)

        self.button_wrong = ctk.CTkButton(self.frame_buttons, text="Falsch", command=self.select_attempt_group, state=tk.DISABLED, font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.button_wrong.pack(side=ctk.LEFT, padx=10)

        self.button_no_attempt = ctk.CTkButton(self.frame_buttons, text="Keine weitere Gruppe", command=self.no_attempt, state=tk.DISABLED, font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.button_no_attempt.pack(side=ctk.LEFT, padx=10)

        self.label_scores = ctk.CTkLabel(self.root, text="Punkte:", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_scores.pack(pady=20)

        # Frame für die Gruppenwahl
        self.frame_group_selection = ctk.CTkFrame(self.root)
        self.frame_group_selection.pack(side=ctk.LEFT, padx=30, pady=30)
        self.frame_group_selection.pack_forget()  # Zuerst verstecken

        self.label_group_selection = ctk.CTkLabel(self.frame_group_selection, text="Welche Gruppe soll es versuchen?", font=("Bahnschrift SemiBold", 16))  # Größere Schriftgröße
        self.label_group_selection.pack()

        self.group_buttons = []

        self.selected_points = 0

    def start_game(self):
        self.selected_dice = None
        self.selected_points = None
        self.button_start.configure(state=ctk.DISABLED)  # Verwende configure anstelle von config
        try:
            num_groups = int(self.entry.get())
            if num_groups < 1 or num_groups > 6:  # Begrenze die Anzahl der Gruppen auf maximal 6
                raise ValueError
            
            self.groups = [{"name": f"Gruppe {i+1}", "points": 0} for i in range(num_groups)]
            self.label_scores.configure(text=self.get_scores())
            self.label_current_group.configure(text=f"Aktuelle Gruppe: {self.groups[self.current_group_index]['name']}")
            self.update_category()  # Kategorie aktualisieren
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige Anzahl an Gruppen (1-6) eingeben.")
    
    def update_category(self):
        # Aktualisieren der aktuellen Kategorie
        if self.current_category_index < len(self.categories):
            self.label_current_category.configure(text=f"Aktuelle Kategorie: {self.categories[self.current_category_index]}")
        else:
            self.label_current_category.configure(text="Keine weiteren Kategorien verfügbar.")
    
    def input_dice(self, dice):
        self.selected_dice = dice
        for btn in self.dice_buttons:
            btn.configure(state=ctk.DISABLED)  # Verwende configure anstelle von config
        self.check_question_display()
    
    def pick_question(self):
        if self.selected_dice is None or self.selected_points is None:
            return
        if not self.questions:
            messagebox.showinfo("Spiel beendet", "Alle Fragen wurden gestellt!")
            self.root.quit()
            return
        
        # Fragen filtern nach der aktuellen Kategorie
        filtered_questions = [q for q in self.questions if q[2] == self.categories[self.current_category_index]]
        
        if not filtered_questions:
            messagebox.showinfo("Keine Fragen", "Es gibt keine Fragen mehr in dieser Kategorie.")
            self.next_turn()
            return
        
        # Wähle die nächste verfügbare Frage
        available_questions = [q for q in filtered_questions if q not in self.used_questions]
        
        if not available_questions:
            messagebox.showinfo("Keine Fragen", "Es gibt keine Fragen mehr in dieser Kategorie.")
            self.next_turn()
            return
        
        # Wähle zufällig eine Frage aus den verfügbaren Fragen
        self.current_question = random.choice(available_questions)
        self.used_questions.append(self.current_question)  # Füge die Frage zur Liste der verwendeten Fragen hinzu
        
        # Überprüfen, ob die Frage tatsächlich ausgewählt wurde
        if self.current_question:
            self.label_question.configure(text=self.current_question[0])  # Frage im Hauptfenster anzeigen
            self.show_question_answer_window()  # Zeige die Antwort im bestehenden Fenster
        else:
            messagebox.showerror("Fehler", "Keine Frage ausgewählt.")
        
        self.button_correct.configure(state=ctk.NORMAL)
        self.button_wrong.configure(state=ctk.NORMAL)
        self.button_no_attempt.configure(state=ctk.NORMAL)

    def show_question_answer_window(self):
        # Erstelle das Fenster für die Frage und Antwort, falls es noch nicht existiert
        if self.question_window is None:
            self.question_window = tk.Toplevel(self.root)
            self.question_window.title("Frage und Antwort")
            
            self.question_label = ctk.CTkLabel(self.question_window, text="", wraplength=800, justify="center", text_color="black", font=("Bahnschrift SemiBold", 24))
            self.question_label.pack(pady=20)
            
            self.answer_label = ctk.CTkLabel(self.question_window, text="", text_color="black", font=("Bahnschrift SemiBold", 24))
            self.answer_label.pack(pady=20)

            close_button = ctk.CTkButton(self.question_window, text="Schließen", command=self.close_question_window, font=("Bahnschrift SemiBold", 24))
            close_button.pack(pady=20)
        
        # Aktualisiere den Text im bestehenden Fenster
        self.question_label.configure(text=self.current_question[0])  # Frage im Frage-Antwort-Fenster anzeigen
        self.answer_label.configure(text=f"Antwort: {self.current_question[1]}")

    def close_question_window(self):
        if self.question_window:
            self.question_window.destroy()
            self.question_window = None  # Setze das Fenster zurück

    def set_points(self, points):
        self.selected_points = points
        for btn in self.point_buttons:
            btn.configure(state=ctk.DISABLED)  # Verwende configure anstelle von config
        self.check_question_display()
    
    def check_question_display(self):
        # Die Frage wird nur angezeigt, wenn sowohl die geworfene Zahl als auch die Punktzahl ausgewählt sind
        if self.selected_dice is not None and self.selected_points is not None:
            self.pick_question()

    def correct_answer(self):
        self.groups[self.current_group_index]["points"] += self.selected_points
        self.next_turn()
    
    def select_attempt_group(self):
        # Zeige das Gruppenwahl-Frame an
        self.frame_group_selection.pack(pady=20)
        
        # Erstelle die Gruppenbuttons
        for btn in self.group_buttons:
            btn.destroy()  # Zerstöre vorherige Buttons, falls vorhanden

        self.group_buttons = []  # Leere die Liste der Buttons
        for i, group in enumerate(self.groups):
            btn = ctk.CTkButton(self.frame_group_selection, text=group['name'], command=lambda i=i: self.attempt_question(i), font=("Bahnschrift SemiBold", 24))  # Größere Schriftgröße
            btn.pack(pady=10)
            self.group_buttons.append(btn)

        # Grau den Text der aktuellen Gruppe aus
        self.label_group_selection.configure(text_color="gray")

    def attempt_question(self, group_index):
        self.selected_attempt_group = group_index
        
        # Punkte abziehen für die aktuelle Gruppe, wenn sie nicht die erste Gruppe ist
        if self.selected_points is not None:
            self.groups[self.current_group_index]["points"] -= self.selected_points
        
        retry = messagebox.askyesno("Chance für andere Gruppe", f"Soll {self.groups[self.selected_attempt_group]['name']} die Frage versuchen?")
        if retry:
            correct = messagebox.askyesno("Antwort", "Hat die andere Gruppe richtig geantwortet?")
            if correct:
                self.groups[self.selected_attempt_group]["points"] += 2  # +2 Punkte für richtig
                # Setze den Text der Gruppenwahl-Box zurück
                self.label_group_selection.configure(text_color="black")
            else:
                self.groups[self.selected_attempt_group]["points"] -= 2  # -2 Punkte für falsch
        
        # Schließe das Gruppenwahl-Frame, nachdem die Frage beantwortet wurde
        self.frame_group_selection.pack_forget()
        
        self.next_turn()

    def no_attempt(self):
        # Punkte abziehen für die aktuelle Gruppe, wenn keine andere Gruppe antwortet
        if self.selected_points is not None:
            self.groups[self.current_group_index]["points"] -= self.selected_points
        
        # Verstecke das Gruppenwahl-Frame
        self.frame_group_selection.pack_forget()
        
        self.next_turn()

    def next_turn(self):
        self.current_group_index = (self.current_group_index + 1) % len(self.groups)
        
        # Wechsel der Kategorie, wenn Gruppe 1 an der Reihe ist
        if self.current_group_index == 0:
            self.current_category_index = (self.current_category_index + 1) % len(self.categories)
            self.update_category()  # Kategorie aktualisieren
        
        self.label_scores.configure(text=self.get_scores())
        self.label_current_group.configure(text=f"Aktuelle Gruppe: {self.groups[self.current_group_index]['name']}")
        self.label_question.configure(text="")  # Frage zurücksetzen
        self.button_correct.configure(state=ctk.DISABLED)
        self.button_wrong.configure(state=ctk.DISABLED)
        self.button_no_attempt.configure(state=ctk.DISABLED)  # Deaktivieren des Buttons für die nächste Runde

        # Zurücksetzen der Auswahl für die nächste Runde
        self.selected_dice = None
        self.selected_points = None
        
        # Aktivieren der Buttons für die nächste Runde
        for btn in self.dice_buttons:
            btn.configure(state=ctk.NORMAL)  # Verwende configure anstelle von config
        for btn in self.point_buttons:
            btn.configure(state=ctk.NORMAL)  # Verwende configure anstelle von config

    def get_scores(self):
        return "\n".join([f"{g['name']}: {g['points']} Punkte" for g in self.groups])

if __name__ == "__main__":
    root = ctk.CTk()
    app = QuizGame(root)
    root.mainloop()
