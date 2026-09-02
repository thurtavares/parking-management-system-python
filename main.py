import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ----------------------------------------------------------------------
# Configurações gerais
# ----------------------------------------------------------------------
TOTAL_VAGAS = 10 # total de vagas do estacionamento
COLUNAS = 5 # quantas vagas por linha no mapa
ARQUIVO_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vagas_fsa2026.json")

COR_LIVRE = "#4CAF50" # verde
COR_OCUPADA = "#E53935" # vermelho
COR_TEXTO = "white"


class Estacionamento:
    """Guarda o estado das vagas, os tickets emitidos, e cuida de salvar/carregar em disco."""

    def __init__(self, total_vagas: int):
        self.total_vagas = total_vagas
        # vagas[str(numero)] = {"nome":, "placa":, "ticket":} ou None se livre
        self.vagas = {str(i): None for i in range(1, total_vagas + 1)}
        # lista de todos os tickets já emitidos (histórico completo)
        # cada item: {"ticket":, "nome":, "placa":, "vaga":, "status": "ocupada"/"liberada"}
        self.historico = []
        self.proximo_ticket = 1
        self.carregar()

    def carregar(self):
        if os.path.exists(ARQUIVO_DADOS):
            try:
                with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                for numero, info in dados.get("vagas", {}).items():
                    if numero in self.vagas:
                        self.vagas[numero] = info
                self.historico = dados.get("historico", [])
                self.proximo_ticket = dados.get("proximo_ticket", 1)
            except (json.JSONDecodeError, OSError):
                pass # se o arquivo estiver corrompido, começa do zero

    def salvar(self):
        dados = {
            "vagas": self.vagas,
            "historico": self.historico,
            "proximo_ticket": self.proximo_ticket,
        }
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def vagas_livres(self):
        return [n for n, info in self.vagas.items() if info is None]

    def placa_ja_registrada(self, placa: str):
        placa = placa.strip().upper()
        for info in self.vagas.values():
            if info and info["placa"].upper() == placa:
                return True
        return False

    def gerar_ticket(self):
        ticket = f"FSA-{self.proximo_ticket:04d}"
        self.proximo_ticket += 1
        return ticket

    def reservar(self, nome: str, placa: str):
        livres = self.vagas_livres()
        if not livres:
            return None, None
        numero = sorted(livres, key=int)[0] # pega a vaga livre de menor número
        ticket = self.gerar_ticket()
        registro = {"nome": nome.strip(), "placa": placa.strip().upper(), "ticket": ticket}
        self.vagas[numero] = registro
        self.historico.append(
            {
                "ticket": ticket,
                "nome": registro["nome"],
                "placa": registro["placa"],
                "vaga": numero,
                "status": "ocupada",
            }
        )
        self.salvar()
        return numero, ticket

    def liberar_vaga(self, numero: str, ticket_informado: str):
        """Tenta liberar a vaga 'numero' se o ticket informado bater com o registrado.
        Retorna True se liberou, False se o ticket estiver errado."""
        info = self.vagas.get(numero)
        if info is None:
            return None # já estava livre
        if info["ticket"].strip().upper() != ticket_informado.strip().upper():
            return False
        self.vagas[numero] = None
        for item in self.historico:
            if item["ticket"] == info["ticket"] and item["status"] == "ocupada":
                item["status"] = "liberada"
                break
        self.salvar()
        return True

    def liberar_tudo(self):
        self.vagas = {str(i): None for i in range(1, self.total_vagas + 1)}
        for item in self.historico:
            if item["status"] == "ocupada":
                item["status"] = "liberada"
        self.salvar()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Estacionamento - Festa de Formatura FSA 2026")
        self.configure(bg="#1c1c2b")
        self.resizable(False, False)

        self.estacionamento = Estacionamento(TOTAL_VAGAS)

        self._montar_abas()

        self.atualizar_mapa()
        self.atualizar_tickets()

    # ------------------------------------------------------------------
    # Montagem da interface
    # ------------------------------------------------------------------
    def _montar_abas(self):
        estilo = ttk.Style(self)
        estilo.theme_use("default")
        estilo.configure("TNotebook", background="#1c1c2b", borderwidth=0)
        estilo.configure(
            "TNotebook.Tab", background="#333", foreground="white", padding=(15, 8), font=("Segoe UI", 10, "bold")
        )
        estilo.map("TNotebook.Tab", background=[("selected", "#FFD700")], foreground=[("selected", "#1c1c2b")])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.aba_mapa = tk.Frame(self.notebook, bg="#1c1c2b")
        self.aba_tickets = tk.Frame(self.notebook, bg="#1c1c2b")

        self.notebook.add(self.aba_mapa, text="🅿️ Mapa do Estacionamento")
        self.notebook.add(self.aba_tickets, text="🎫 Tickets")

        self._montar_cabecalho()
        self._montar_formulario()
        self._montar_mapa()
        self._montar_rodape()
        self._montar_aba_tickets()

    def _montar_cabecalho(self):
        tk.Label(
            self.aba_mapa,
            text="🎓 Bem-vindo à Festa de Formatura da FSA 2026! 🎓",
            font=("Segoe UI", 16, "bold"),
            bg="#1c1c2b",
            fg="#FFD700",
            pady=15,
        ).pack(fill="x")

        tk.Label(
            self.aba_mapa,
            text="Informe seu nome e a placa do veículo para reservar sua vaga\n"
            "Clique em uma vaga ocupada para liberá-la com o código do ticket",
            font=("Segoe UI", 10),
            bg="#1c1c2b",
            fg="white",
            justify="center",
        ).pack(pady=(0, 10))

    def _montar_formulario(self):
        frame = tk.Frame(self.aba_mapa, bg="#1c1c2b")
        frame.pack(pady=5)

        tk.Label(frame, text="Nome:", bg="#1c1c2b", fg="white", font=("Segoe UI", 10)).grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.entrada_nome = tk.Entry(frame, width=25, font=("Segoe UI", 10))
        self.entrada_nome.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="Placa:", bg="#1c1c2b", fg="white", font=("Segoe UI", 10)).grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        self.entrada_placa = tk.Entry(frame, width=12, font=("Segoe UI", 10))
        self.entrada_placa.grid(row=0, column=3, padx=5, pady=5)

        botao = tk.Button(
            frame,
            text="Reservar vaga",
            font=("Segoe UI", 10, "bold"),
            bg="#FFD700",
            fg="#1c1c2b",
            command=self.reservar_vaga,
        )
        botao.grid(row=0, column=4, padx=10, pady=5)

        # Enter no campo placa também reserva
        self.entrada_placa.bind("<Return>", lambda e: self.reservar_vaga())
        self.entrada_nome.bind("<Return>", lambda e: self.entrada_placa.focus())

    def _montar_mapa(self):
        self.frame_mapa = tk.Frame(self.aba_mapa, bg="#1c1c2b", padx=15, pady=15)
        self.frame_mapa.pack()

        self.celulas = {} # numero_da_vaga -> Label
        linhas = (TOTAL_VAGAS + COLUNAS - 1) // COLUNAS

        numero = 1
        for linha in range(linhas):
            for coluna in range(COLUNAS):
                if numero > TOTAL_VAGAS:
                    break
                celula = tk.Label(
                    self.frame_mapa,
                    text="",
                    width=16,
                    height=4,
                    font=("Segoe UI", 9, "bold"),
                    relief="ridge",
                    bd=2,
                    justify="center",
                    cursor="hand2",
                )
                celula.grid(row=linha, column=coluna, padx=6, pady=6)
                celula.bind("<Button-1>", lambda e, n=str(numero): self.clicar_vaga(n))
                self.celulas[str(numero)] = celula
                numero += 1

    def _montar_rodape(self):
        self.label_status = tk.Label(
            self.aba_mapa,
            text="",
            font=("Segoe UI", 12, "bold"),
            bg="#1c1c2b",
            fg="#4CAF50",
            pady=10,
        )
        self.label_status.pack()

        tk.Button(
            self.aba_mapa,
            text="Reiniciar estacionamento (limpar todas as vagas)",
            font=("Segoe UI", 8),
            bg="#333",
            fg="white",
            command=self.reiniciar,
        ).pack(pady=(0, 10))

    def _montar_aba_tickets(self):
        tk.Label(
            self.aba_tickets,
            text="🎫 Todos os Tickets Emitidos",
            font=("Segoe UI", 14, "bold"),
            bg="#1c1c2b",
            fg="#FFD700",
            pady=15,
        ).pack(fill="x")

        frame_tabela = tk.Frame(self.aba_tickets, bg="#1c1c2b", padx=15, pady=5)
        frame_tabela.pack(fill="both", expand=True)

        colunas = ("ticket", "nome", "placa", "vaga", "status")
        self.tabela_tickets = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=12)

        self.tabela_tickets.heading("ticket", text="Ticket")
        self.tabela_tickets.heading("nome", text="Nome")
        self.tabela_tickets.heading("placa", text="Placa")
        self.tabela_tickets.heading("vaga", text="Vaga")
        self.tabela_tickets.heading("status", text="Status")

        self.tabela_tickets.column("ticket", width=90, anchor="center")
        self.tabela_tickets.column("nome", width=200, anchor="w")
        self.tabela_tickets.column("placa", width=100, anchor="center")
        self.tabela_tickets.column("vaga", width=70, anchor="center")
        self.tabela_tickets.column("status", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela_tickets.yview)
        self.tabela_tickets.configure(yscrollcommand=scrollbar.set)

        self.tabela_tickets.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tabela_tickets.tag_configure("ocupada", background="#E53935", foreground="white")
        self.tabela_tickets.tag_configure("liberada", background="#2e2e2e", foreground="#4CAF50")

        tk.Button(
            self.aba_tickets,
            text="Atualizar lista",
            font=("Segoe UI", 9),
            bg="#333",
            fg="white",
            command=self.atualizar_tickets,
        ).pack(pady=10)

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------
    def reservar_vaga(self):
        nome = self.entrada_nome.get().strip()
        placa = self.entrada_placa.get().strip()

        if not nome or not placa:
            messagebox.showwarning("Dados incompletos", "Por favor, preencha nome e placa.")
            return

        if self.estacionamento.placa_ja_registrada(placa):
            messagebox.showwarning(
                "Placa já registrada", f"A placa {placa.upper()} já possui uma vaga reservada."
            )
            return

        numero, ticket = self.estacionamento.reservar(nome, placa)

        if numero is None:
            messagebox.showinfo(
                "Estacionamento lotado",
                "Que pena! Não há mais vagas disponíveis no estacionamento. 😔",
            )
            return

        messagebox.showinfo(
            "Vaga reservada!",
            f"🎉 Vaga {numero} reservada para {nome}!\n"
            f"Placa: {placa.upper()}\n\n"
            f"🎫 Seu ticket é: {ticket}\n"
            f"Guarde esse código — ele será necessário para liberar a vaga.",
        )

        self.entrada_nome.delete(0, tk.END)
        self.entrada_placa.delete(0, tk.END)
        self.entrada_nome.focus()

        self.atualizar_mapa()
        self.atualizar_tickets()

    def clicar_vaga(self, numero: str):
        info = self.estacionamento.vagas[numero]
        if info is None:
            messagebox.showinfo("Vaga livre", f"A vaga {numero} já está livre.")
            return

        ticket_informado = simpledialog.askstring(
            "Liberar vaga",
            f"Vaga {numero} está ocupada por {info['nome']} (placa {info['placa']}).\n"
            f"Digite o código do ticket para liberar essa vaga:",
            parent=self,
        )

        if ticket_informado is None:
            return # usuário cancelou

        resultado = self.estacionamento.liberar_vaga(numero, ticket_informado)

        if resultado is True:
            messagebox.showinfo("Vaga liberada", f"✅ A vaga {numero} foi liberada com sucesso!")
            self.atualizar_mapa()
            self.atualizar_tickets()
        elif resultado is False:
            messagebox.showerror("Código incorreto", "O código do ticket informado não confere com esta vaga.")

    def reiniciar(self):
        resposta = messagebox.askyesno(
            "Confirmar reinício",
            "Tem certeza que deseja liberar TODAS as vagas? Essa ação não pode ser desfeita.",
        )
        if resposta:
            self.estacionamento.liberar_tudo()
            self.atualizar_mapa()
            self.atualizar_tickets()

    def atualizar_mapa(self):
        for numero, celula in self.celulas.items():
            info = self.estacionamento.vagas[numero]
            if info is None:
                celula.configure(
                    text=f"Vaga {numero}\n\nLIVRE",
                    bg=COR_LIVRE,
                    fg=COR_TEXTO,
                )
            else:
                celula.configure(
                    text=f"Vaga {numero}\n{info['nome']}\nPlaca: {info['placa']}\nTicket: {info['ticket']}",
                    bg=COR_OCUPADA,
                    fg=COR_TEXTO,
                )

        restantes = len(self.estacionamento.vagas_livres())
        if restantes == 0:
            self.label_status.configure(
                text="🚫 Estacionamento LOTADO — 0 vagas restantes", fg="#E53935"
            )
        else:
            self.label_status.configure(
                text=f"✅ Vagas restantes: {restantes} de {TOTAL_VAGAS}", fg="#4CAF50"
            )

    def atualizar_tickets(self):
        for item in self.tabela_tickets.get_children():
            self.tabela_tickets.delete(item)

        for registro in self.estacionamento.historico:
            tag = "ocupada" if registro["status"] == "ocupada" else "liberada"
            status_texto = "Ocupada" if registro["status"] == "ocupada" else "Liberada"
            self.tabela_tickets.insert(
                "",
                "end",
                values=(registro["ticket"], registro["nome"], registro["placa"], registro["vaga"], status_texto),
                tags=(tag,),
            )


if __name__ == "__main__":
    app = App()
    app.mainloop()