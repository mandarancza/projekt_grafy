import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
import ast # Do bezpiecznego parsowania stringu jako słownika Pythona

# --- Funkcja algorytmu znajdującego najkrótszy cykl (z poprzedniej odpowiedzi) ---
def min_cykl(graph):
    min_dlugosc_cyklu = float('inf')
    najkrotszy_cykl_sciezka = []

    if not graph:
        return float('inf'), []

    # Pobieramy wszystkie unikalne węzły z grafu
    wszystkie_wezly_zbior = set(graph.keys())
    for sasiedzi_lista in graph.values():
        for sasiad_wezel in sasiedzi_lista:
            wszystkie_wezly_zbior.add(sasiad_wezel)
    
    nodes = list(wszystkie_wezly_zbior)
    if not nodes:
        return float('inf'), []

    for start_node in nodes:
        queue = collections.deque([(start_node, [start_node])])
        odwiedzone_w_tym_bfs = {start_node} # Resetowane dla każdego BFS

        while queue:
            biezacy_wezel, sciezka = queue.popleft()

            # Optymalizacja: długość cyklu to liczba krawędzi, czyli len(sciezka)
            # Jeśli ścieżka ma N węzłów, to cykl zamykający się do start_node będzie miał N krawędzi.
            if len(sciezka) >= min_dlugosc_cyklu:
                continue

            for sasiad in graph.get(biezacy_wezel, []):
                if sasiad == start_node:
                    dlugosc_tego_cyklu = len(sciezka) # Np. [A,B,C] -> A-B, B-C, C-A (3 krawędzie)
                    if dlugosc_tego_cyklu < min_dlugosc_cyklu:
                        min_dlugosc_cyklu = dlugosc_tego_cyklu
                        najkrotszy_cykl_sciezka = sciezka + [start_node]
                
                elif sasiad not in odwiedzone_w_tym_bfs:
                    odwiedzone_w_tym_bfs.add(sasiad)
                    queue.append((sasiad, sciezka + [sasiad]))

    if min_dlugosc_cyklu == float('inf'):
        return float('inf'), []
    
    return min_dlugosc_cyklu, najkrotszy_cykl_sciezka
# --- Koniec funkcji algorytmu ---


class GraphCycleApp:
    def __init__(self, master):
        self.master = master
        master.title("Najkrótszy Cykl w Grafie Skierowanym")
        master.geometry("900x750")

        # --- Ramka dla kontrolek ---
        control_frame = tk.Frame(master, pady=10)
        control_frame.pack(fill=tk.X)

        tk.Label(control_frame, text="Definicja grafu (słownik Pythona):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.graph_input_text = scrolledtext.ScrolledText(control_frame, height=6, width=60)
        self.graph_input_text.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.graph_input_text.insert(tk.INSERT, "{0: [1, 2], 1: [2], 2: [0, 3], 3: [4], 4: [1]}") # Przykładowy graf
        
        button_frame = tk.Frame(control_frame) # Ramka dla przycisków obok pola tekstowego
        button_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ns")

        self.find_button = tk.Button(button_frame, text="Znajdź Najkrótszy Cykl", command=self.process_graph_and_draw)
        self.find_button.pack(fill=tk.X, pady=2)

        self.clear_button = tk.Button(button_frame, text="Wyczyść Graf", command=self.clear_graph_visualization)
        self.clear_button.pack(fill=tk.X, pady=2)
        
        self.load_example_button = tk.Button(button_frame, text="Załaduj Przykład", command=self.load_example_graph)
        self.load_example_button.pack(fill=tk.X, pady=2)

        control_frame.grid_columnconfigure(0, weight=1) # Pozwala polu tekstowemu się rozciągać

        # --- Ramka dla wyników ---
        result_frame = tk.Frame(master, pady=5)
        result_frame.pack(fill=tk.X)
        
        self.result_label = tk.Label(result_frame, text="Wynik: ", font=("Arial", 10))
        self.result_label.pack(side=tk.LEFT, padx=5)

        # --- Ramka dla wizualizacji grafu ---
        self.graph_frame = tk.Frame(master)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.axis('off') 
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.draw()

        self.current_graph_dict = None
        self.current_nx_graph = None
        self.current_pos = None # Przechowuje układ węzłów dla spójności rysowania

    def parse_graph_input(self):
        input_str = self.graph_input_text.get("1.0", tk.END).strip()
        if not input_str:
            messagebox.showerror("Błąd", "Pole wprowadzania grafu jest puste.")
            return None
        try:
            graph_dict = ast.literal_eval(input_str)
            if not isinstance(graph_dict, dict):
                messagebox.showerror("Błąd", "Niepoprawny format grafu. Oczekiwano słownika.")
                return None
            # Prosta walidacja formatu wartości (powinny być listami)
            for key, value in graph_dict.items():
                if not isinstance(value, list):
                    messagebox.showerror("Błąd", f"Wartość dla klucza '{key}' musi być listą sąsiadów.")
                    return None
            return graph_dict
        except (SyntaxError, ValueError) as e:
            messagebox.showerror("Błąd parsowania", f"Nie można sparsować grafu: {e}\nUpewnij się, że format to poprawny słownik Pythona, np. {{'A': ['B'], 'B': ['A']}} lub {{0: [1], 1: [0]}}.")
            return None

    def draw_graph(self, graph_dict_to_draw, cycle_path=None):
        self.ax.clear()

        if not graph_dict_to_draw:
            self.ax.text(0.5, 0.5, "Wprowadź definicję grafu i kliknij 'Znajdź Cykl'", 
                         ha='center', va='center', fontsize=10, wrap=True)
            self.ax.axis('off')
            self.canvas.draw()
            self.current_nx_graph = None
            self.current_pos = None
            return

        G = nx.DiGraph()
        
        all_nodes_in_def = set(graph_dict_to_draw.keys())
        for neighbors in graph_dict_to_draw.values():
            all_nodes_in_def.update(neighbors)
        
        for node in all_nodes_in_def:
            G.add_node(node)
        
        for node, neighbors in graph_dict_to_draw.items():
            for neighbor in neighbors:
                G.add_edge(node, neighbor)
        
        self.current_nx_graph = G

        # Utrzymanie pozycji węzłów, jeśli graf jest ten sam lub podobny
        # lub wygenerowanie nowych, jeśli graf się zmienił znacząco
        # Proste sprawdzenie: jeśli liczba węzłów się zmieniła lub current_pos nie istnieje
        if self.current_pos is None or set(self.current_pos.keys()) != set(G.nodes()):
            self.current_pos = nx.spring_layout(G, seed=42, k=0.5, iterations=50) # k i iterations dla lepszego rozłożenia
            # Inne opcje: nx.circular_layout(G), nx.kamada_kawai_layout(G), nx.shell_layout(G)

        node_colors = ['skyblue'] * G.number_of_nodes()
        edge_colors = ['gray'] * G.number_of_edges()
        edge_widths = [1.5] * G.number_of_edges()

        # Tworzymy mapowanie węzłów na indeksy listy G.nodes() dla kolorowania
        node_list_for_coloring = list(G.nodes()) # Kolejność zgodna z tym, jak nx.draw je traktuje
        node_to_idx_map = {node: i for i, node in enumerate(node_list_for_coloring)}

        if cycle_path and len(cycle_path) > 1:
            # Podświetl węzły w cyklu
            for node_in_cycle in cycle_path[:-1]: # Ostatni węzeł to powtórzenie pierwszego
                if node_in_cycle in node_to_idx_map:
                     node_colors[node_to_idx_map[node_in_cycle]] = 'salmon'
            
            # Podświetl krawędzie w cyklu
            cycle_edges_set = set()
            for i in range(len(cycle_path) - 1):
                u, v = cycle_path[i], cycle_path[i+1]
                cycle_edges_set.add((u,v))

            edge_list_for_coloring = list(G.edges())
            for i, edge in enumerate(edge_list_for_coloring):
                if edge in cycle_edges_set:
                    edge_colors[i] = 'red'
                    edge_widths[i] = 3.0
        
        nx.draw(G, self.current_pos, ax=self.ax, with_labels=True, 
                node_color=node_colors, 
                edge_color=edge_colors, 
                width=edge_widths,
                node_size=600, 
                font_size=9, 
                arrows=True, arrowstyle='-|>', arrowsize=12, connectionstyle='arc3,rad=0.1')

        self.ax.axis('off')
        self.canvas.draw()

    def process_graph_and_draw(self):
        graph_dict = self.parse_graph_input()
        if graph_dict is None:
            self.current_graph_dict = None # Resetuj, jeśli parsowanie nie powiodło się
            self.draw_graph(None) 
            self.result_label.config(text="Wynik: Błąd w danych wejściowych.")
            return

        self.current_graph_dict = graph_dict # Zapisz aktualny graf
        
        # Najpierw narysuj graf (lub przerysuj, jeśli już istnieje)
        self.draw_graph(self.current_graph_dict) # Rysuj bez podświetlenia na początku

        dlugosc, sciezka = min_cykl(self.current_graph_dict)

        if dlugosc == float('inf'):
            self.result_label.config(text="Wynik: Brak cyklu w grafie.")
            # Graf już narysowany, nie trzeba podświetlać cyklu
        else:
            sciezka_str = " -> ".join(map(str, sciezka))
            self.result_label.config(text=f"Wynik: Najkrótszy cykl ma długość {dlugosc}. Ścieżka: {sciezka_str}")
            # Ponownie narysuj graf, tym razem z podświetlonym cyklem
            self.draw_graph(self.current_graph_dict, cycle_path=sciezka)

    def clear_graph_visualization(self):
        self.graph_input_text.delete("1.0", tk.END)
        self.current_graph_dict = None
        self.draw_graph(None) # Wyczyść płótno
        self.result_label.config(text="Wynik: ")

    def load_example_graph(self):
        # Można dodać więcej przykładów lub okno dialogowe do wyboru
        example_graphs = {
            "Prosty cykl (3 węzły)": "{'A': ['B'], 'B': ['C'], 'C': ['A']}",
            "Cykl z pętlą własną": "{'X': ['Y'], 'Y': ['Y']}",
            "Dłuższy cykl (4 węzły)": "{0: [1], 1: [2], 2: [3], 3: [0]}",
            "Graf z kilkoma cyklami": "{'A':['B','E'], 'B':['C'], 'C':['A','D'], 'D':['E'], 'E':['C','F'], 'F':[]}",
            "Graf bez cykli": "{'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []}",
            "Graf z przykładu 1": "{0: [1, 2], 1: [2], 2: [0, 3], 3: [4], 4: [1]}"
        }
        
        # Prosty wybór - można rozbudować o okno dialogowe
        choice = simpledialog.askstring("Wybierz przykład", 
                                        "Wpisz numer przykładu lub nazwę:\n" + 
                                        "\n".join([f"{i+1}. {name}" for i, name in enumerate(example_graphs.keys())]) +
                                        "\nLub wybierz losowy (wpisz 'losowy')",
                                        parent=self.master)
        
        selected_graph_str = None
        if choice:
            if choice.lower() == 'losowy':
                import random
                selected_graph_str = random.choice(list(example_graphs.values()))
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(example_graphs):
                        selected_graph_str = list(example_graphs.values())[idx]
                    else: # Spróbuj dopasować po nazwie
                        for name, graph_str_val in example_graphs.items():
                            if choice.lower() in name.lower():
                                selected_graph_str = graph_str_val
                                break
                except ValueError: # Jeśli nie jest liczbą, szukaj po nazwie
                    for name, graph_str_val in example_graphs.items():
                        if choice.lower() in name.lower():
                            selected_graph_str = graph_str_val
                            break
            
            if selected_graph_str:
                self.graph_input_text.delete("1.0", tk.END)
                self.graph_input_text.insert(tk.INSERT, selected_graph_str)
                self.process_graph_and_draw() # Automatycznie przetwórz i narysuj
            else:
                messagebox.showinfo("Informacja", "Nie znaleziono przykładu o podanej nazwie/numerze.")


def main():
    root = tk.Tk()
    app = GraphCycleApp(root)
            
    root.mainloop()

if __name__ == '__main__':
    main()