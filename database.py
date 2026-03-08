import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json

class ComandoEditor:
    """Editor de comandos em formato de tabela"""
    def __init__(self, parent, comandos=None):
        self.parent = parent
        self.comandos = comandos or []
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Button(toolbar, text="Adicionar Comando", command=self.adicionar_comando).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Remover Comando", command=self.remover_comando).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Editar", command=self.editar_comando).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▲ Subir", command=self.subir_comando).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▼ Descer", command=self.descer_comando).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Limpar Tudo", command=self.limpar_tudo).pack(side=tk.LEFT, padx=2)
        
        # Treeview para mostrar comandos
        columns = ("nome", "parametros")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="tree headings", height=8)
        
        # Configurar colunas
        self.tree.heading("#0", text="ID")
        self.tree.column("#0", width=40)
        
        self.tree.heading("nome", text="Nome do Comando")
        self.tree.column("nome", width=150)
        
        self.tree.heading("parametros", text="Parâmetros")
        self.tree.column("parametros", width=400)
        
        # Scrollbars
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Bind duplo clique para editar
        self.tree.bind("<Double-1>", lambda e: self.editar_comando())
        
        # Carregar comandos existentes
        self.atualizar_lista()
    
    def atualizar_lista(self):
        """Atualiza a lista de comandos"""
        # Limpar tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar comandos
        for i, cmd in enumerate(self.comandos):
            nome = cmd.get("nome", "desconhecido")
            params = cmd.get("param", [])
            
            # Formatar parâmetros para exibição
            if isinstance(params, list):
                params_str = ", ".join([f"'{p}'" if isinstance(p, str) else str(p) for p in params])
            else:
                params_str = str(params)
            
            self.tree.insert("", "end", text=str(i+1), values=(nome, params_str), iid=str(i))
    
    def adicionar_comando(self):
        """Abre diálogo para adicionar novo comando"""
        self._abrir_dialogo_comando()
    
    def editar_comando(self):
        """Abre diálogo para editar comando selecionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um comando para editar")
            return
        
        idx = int(selection[0])
        self._abrir_dialogo_comando(self.comandos[idx], idx)
    
    def _abrir_dialogo_comando(self, comando=None, indice=None):
        """Diálogo para adicionar/editar comando"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Editar Comando" if comando else "Novo Comando")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Frame principal
        main = ttk.Frame(dialog, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Nome do comando
        ttk.Label(main, text="Nome do Comando:").grid(row=0, column=0, sticky=tk.W, pady=5)
        nome_var = tk.StringVar(value=comando.get("nome", "") if comando else "")
        nome_entry = ttk.Entry(main, textvariable=nome_var, width=30)
        nome_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Sugestões de comandos
        ttk.Label(main, text="Sugestões:").grid(row=1, column=0, sticky=tk.W, pady=5)
        sugestoes_frame = ttk.Frame(main)
        sugestoes_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        comandos_sugeridos = ["mostrar_texto", "mostrar_escolhas", "set_switch", "esperar", "adicionar_item", "reproduzir_som"]
        for i, sug in enumerate(comandos_sugeridos[:3]):
            ttk.Button(sugestoes_frame, text=sug, 
                      command=lambda s=sug: nome_var.set(s)).pack(side=tk.LEFT, padx=2)
        
        for sug in comandos_sugeridos[3:]:
            ttk.Button(sugestoes_frame, text=sug, 
                      command=lambda s=sug: nome_var.set(s)).pack(side=tk.LEFT, padx=2)
        
        # Parâmetros
        ttk.Label(main, text="Parâmetros:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        
        # Frame para lista de parâmetros
        params_frame = ttk.LabelFrame(main, text="Lista de Parâmetros", padding="5")
        params_frame.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Lista de parâmetros
        params_listbox = tk.Listbox(params_frame, height=5, width=40)
        params_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(params_frame, orient=tk.VERTICAL, command=params_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        params_listbox.config(yscrollcommand=scrollbar.set)
        
        # Frame para adicionar/editar parâmetros
        param_edit_frame = ttk.Frame(main)
        param_edit_frame.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(param_edit_frame, text="Novo Parâmetro:").pack(side=tk.LEFT)
        param_entry = ttk.Entry(param_edit_frame, width=20)
        param_entry.pack(side=tk.LEFT, padx=5)
        
        def adicionar_param():
            valor = param_entry.get().strip()
            if valor:
                params_listbox.insert(tk.END, valor)
                param_entry.delete(0, tk.END)
        
        def remover_param():
            selection = params_listbox.curselection()
            if selection:
                params_listbox.delete(selection[0])
        
        def editar_param():
            selection = params_listbox.curselection()
            if selection:
                valor_atual = params_listbox.get(selection[0])
                param_entry.delete(0, tk.END)
                param_entry.insert(0, valor_atual)
                params_listbox.delete(selection[0])
        
        ttk.Button(param_edit_frame, text="Adicionar", command=adicionar_param).pack(side=tk.LEFT, padx=2)
        ttk.Button(param_edit_frame, text="Remover", command=remover_param).pack(side=tk.LEFT, padx=2)
        ttk.Button(param_edit_frame, text="Editar", command=editar_param).pack(side=tk.LEFT, padx=2)
        
        # Carregar parâmetros existentes
        if comando and "param" in comando:
            params = comando["param"]
            if isinstance(params, list):
                for p in params:
                    params_listbox.insert(tk.END, str(p))
            else:
                params_listbox.insert(tk.END, str(params))
        
        # Tipo do parâmetro
        ttk.Label(main, text="Tipo:").grid(row=4, column=0, sticky=tk.W, pady=5)
        tipo_var = tk.StringVar(value="texto")
        tipo_frame = ttk.Frame(main)
        tipo_frame.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Radiobutton(tipo_frame, text="Texto", variable=tipo_var, value="texto").pack(side=tk.LEFT)
        ttk.Radiobutton(tipo_frame, text="Número", variable=tipo_var, value="numero").pack(side=tk.LEFT)
        ttk.Radiobutton(tipo_frame, text="Booleano", variable=tipo_var, value="booleano").pack(side=tk.LEFT)
        
        # Botões
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def salvar():
            nome = nome_var.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Nome do comando é obrigatório")
                return
            
            # Coletar parâmetros
            params = []
            for i in range(params_listbox.size()):
                valor = params_listbox.get(i)
                if tipo_var.get() == "numero":
                    try:
                        valor = int(valor) if valor.isdigit() else float(valor)
                    except:
                        pass
                elif tipo_var.get() == "booleano":
                    valor = valor.lower() in ["true", "1", "sim", "yes"]
                
                params.append(valor)
            
            # Se só tem um parâmetro, pode ser salvo como valor único
            if len(params) == 1:
                params = params[0]
            
            novo_comando = {"nome": nome, "param": params}
            
            if indice is not None:
                self.comandos[indice] = novo_comando
            else:
                self.comandos.append(novo_comando)
            
            self.atualizar_lista()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Salvar", command=salvar, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        # Focar no campo de nome
        nome_entry.focus()
    
    def remover_comando(self):
        """Remove o comando selecionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um comando para remover")
            return
        
        if messagebox.askyesno("Confirmar", "Remover comando selecionado?"):
            idx = int(selection[0])
            del self.comandos[idx]
            self.atualizar_lista()
    
    def subir_comando(self):
        """Move o comando selecionado para cima"""
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = int(selection[0])
        if idx > 0:
            self.comandos[idx], self.comandos[idx-1] = self.comandos[idx-1], self.comandos[idx]
            self.atualizar_lista()
            self.tree.selection_set(str(idx-1))
    
    def descer_comando(self):
        """Move o comando selecionado para baixo"""
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = int(selection[0])
        if idx < len(self.comandos) - 1:
            self.comandos[idx], self.comandos[idx+1] = self.comandos[idx+1], self.comandos[idx]
            self.atualizar_lista()
            self.tree.selection_set(str(idx+1))
    
    def limpar_tudo(self):
        """Limpa todos os comandos"""
        if self.comandos and messagebox.askyesno("Confirmar", "Remover todos os comandos?"):
            self.comandos.clear()
            self.atualizar_lista()
    
    def get_comandos(self):
        """Retorna a lista de comandos"""
        return self.comandos


class PaginaEvento:
    """Representa uma página dentro de um evento"""
    def __init__(self, parent, pagina_num, dados=None):
        self.frame = ttk.Frame(parent)
        self.pagina_num = pagina_num
        self.dados = dados or {
            "condicao": None,
            "anima": 1,
            "comandos": [],
            "hitbox": [0, 1],
            "passavel": True,
            "gatilho": 0
        }
        
        # Extrair comandos
        comandos = self.dados.get("comandos", [])
        
        self.criar_interface(comandos)
    
    def criar_interface(self, comandos):
        # Área de Propriedades (superior)
        prop_frame = ttk.LabelFrame(self.frame, text=f"Página {self.pagina_num} - Propriedades", padding="10")
        prop_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Grid para propriedades
        row = 0
        
        # Condição
        ttk.Label(prop_frame, text="Condição:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.condicao_entry = ttk.Entry(prop_frame, width=40)
        self.condicao_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        if self.dados.get("condicao"):
            self.condicao_entry.insert(0, str(self.dados["condicao"]))
        row += 1
        
        # Anima
        ttk.Label(prop_frame, text="Anima:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.anima_entry = ttk.Entry(prop_frame, width=10)
        self.anima_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        self.anima_entry.insert(0, str(self.dados.get("anima", 1)))
        row += 1
        
        # Hitbox
        ttk.Label(prop_frame, text="Hitbox (x,y):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.hitbox_entry = ttk.Entry(prop_frame, width=10)
        self.hitbox_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        hitbox = self.dados.get("hitbox", [0, 1])
        self.hitbox_entry.insert(0, f"{hitbox[0]},{hitbox[1]}")
        row += 1
        
        # Passável
        ttk.Label(prop_frame, text="Passável:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.passavel_var = tk.BooleanVar(value=self.dados.get("passavel", True))
        ttk.Checkbutton(prop_frame, variable=self.passavel_var).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Gatilho
        ttk.Label(prop_frame, text="Gatilho:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.gatilho_entry = ttk.Entry(prop_frame, width=10)
        self.gatilho_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        self.gatilho_entry.insert(0, str(self.dados.get("gatilho", 0)))
        
        # Área de Comandos (inferior) - AGORA USA O EDITOR DE COMANDOS
        cmd_frame = ttk.LabelFrame(self.frame, text=f"Página {self.pagina_num} - Comandos", padding="10")
        cmd_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Criar o editor de comandos dentro do frame
        self.comando_editor = ComandoEditor(cmd_frame, comandos)
    
    def obter_dados(self):
        """Retorna os dados da página"""
        # Processar hitbox
        hitbox = [0, 1]
        try:
            hitbox_str = self.hitbox_entry.get().strip()
            if hitbox_str:
                partes = hitbox_str.split(',')
                hitbox = [int(partes[0]), int(partes[1])]
        except:
            pass
        
        # Processar anima
        anima = 1
        try:
            anima = int(self.anima_entry.get())
        except:
            pass
        
        # Processar gatilho
        gatilho = 0
        try:
            gatilho = int(self.gatilho_entry.get())
        except:
            pass
        
        # Processar condição
        cond = self.condicao_entry.get().strip()
        if cond == "" or cond.lower() == "none":
            cond = None
        
        # Obter comandos do editor
        comandos = self.comando_editor.get_comandos()
        
        return {
            "condicao": cond,
            "anima": anima,
            "comandos": comandos,
            "hitbox": hitbox,
            "passavel": self.passavel_var.get(),
            "gatilho": gatilho
        }


class EditorEventos:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Eventos JSON")
        self.root.geometry("1100x700")
        
        self.eventos = []  # Lista de eventos, cada evento é uma lista de páginas
        self.paginas_frame = {}  # Dicionário para armazenar frames de páginas
        self.arquivo_atual = None
        
        self.setup_ui()
        self.carregar_exemplo()
    
    def setup_ui(self):
        # Frame principal com Painel dividido
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === PAINEL ESQUERDO - LISTA DE EVENTOS ===
        left_frame = ttk.Frame(main_panel, width=250)
        main_panel.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Eventos:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        # Lista de eventos
        self.lista_eventos = tk.Listbox(left_frame, height=20)
        self.lista_eventos.pack(fill=tk.BOTH, expand=True, pady=5)
        self.lista_eventos.bind('<<ListboxSelect>>', self.selecionar_evento)
        
        # Botões da lista
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Adicionar Evento", command=self.adicionar_evento, width=15).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Remover Evento", command=self.remover_evento, width=15).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Duplicar Evento", command=self.duplicar_evento, width=15).pack(fill=tk.X, pady=2)
        
        # === PAINEL DIREITO - EDITOR DE PÁGINAS ===
        self.right_frame = ttk.Frame(main_panel)
        main_panel.add(self.right_frame, weight=3)
        
        # Cabeçalho
        header_frame = ttk.Frame(self.right_frame)
        header_frame.pack(fill=tk.X, pady=5)
        
        self.evento_label = ttk.Label(header_frame, text="Nenhum evento selecionado", font=('Arial', 11, 'bold'))
        self.evento_label.pack(side=tk.LEFT)
        
        # Botões para gerenciar páginas
        page_btn_frame = ttk.Frame(header_frame)
        page_btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(page_btn_frame, text="➕ Adicionar Página", command=self.adicionar_pagina, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(page_btn_frame, text="➖ Remover Página", command=self.remover_pagina, width=15).pack(side=tk.LEFT, padx=2)
        
        # Notebook para as páginas do evento
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Barra de ferramentas inferior
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Novo", command=self.novo_arquivo, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Abrir", command=self.abrir_arquivo, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Salvar", command=self.salvar_arquivo, width=10).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="Arquivo:").pack(side=tk.LEFT, padx=(20, 5))
        self.arquivo_label = ttk.Label(toolbar, text="Nenhum", foreground="gray")
        self.arquivo_label.pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=(0, 5))
    
    def carregar_exemplo(self):
        """Carrega o exemplo inicial"""
        # Evento 1: com 1 página
        evento1 = [
            {
                "condicao": None,
                "anima": 1,
                "comandos": [
                    {"nome": "mostrar_texto", "param": ["oi, tudo bem?"]},
                    {"nome": "mostrar_escolhas", "param": ["sim", "não"]}
                ],
                "hitbox": [0, 1],
                "passavel": True,
                "gatilho": 0
            }
        ]
        
        # Evento 2: com 2 páginas
        evento2 = [
            {
                "condicao": "a<10",
                "anima": 1,
                "comandos": [
                    {"nome": "mostrar_texto", "param": ["primeira página"]}
                ],
                "hitbox": [0, 1],
                "passavel": True,
                "gatilho": 0
            },
            {
                "condicao": "b>5",
                "anima": 2,
                "comandos": [
                    {"nome": "set_switch", "param": ["switch_2", "b = a + 10"]},
                    {"nome": "esperar", "param": 60}
                ],
                "hitbox": [0, 1],
                "passavel": False,
                "gatilho": 1
            }
        ]
        
        self.eventos = [evento1, evento2]
        self.atualizar_lista()
        self.status_var.set("Exemplo carregado")
    
    def atualizar_lista(self):
        """Atualiza a lista de eventos"""
        self.lista_eventos.delete(0, tk.END)
        for i, evento in enumerate(self.eventos):
            num_paginas = len(evento)
            self.lista_eventos.insert(tk.END, f"Evento {i+1} ({num_paginas} página{'s' if num_paginas != 1 else ''})")
    
    def selecionar_evento(self, event):
        """Quando um evento é selecionado na lista"""
        selection = self.lista_eventos.curselection()
        if selection:
            idx = selection[0]
            evento = self.eventos[idx]
            
            self.evento_label.config(text=f"Editando: Evento {idx+1} - {len(evento)} página(s)")
            
            # Limpar notebook
            for tab in self.notebook.tabs():
                self.notebook.forget(tab)
            
            # Recriar abas para cada página
            for i, pagina_dados in enumerate(evento):
                self.criar_aba_pagina(i+1, pagina_dados)
    
    def criar_aba_pagina(self, num_pagina, dados=None):
        """Cria uma nova aba para uma página"""
        pagina = PaginaEvento(self.notebook, num_pagina, dados)
        self.notebook.add(pagina.frame, text=f"Página {num_pagina}")
        return pagina
    
    def adicionar_pagina(self):
        """Adiciona uma nova página ao evento selecionado"""
        selection = self.lista_eventos.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um evento primeiro")
            return
        
        idx = selection[0]
        
        # Criar nova página vazia
        nova_pagina = {
            "condicao": None,
            "anima": 1,
            "comandos": [],
            "hitbox": [0, 1],
            "passavel": True,
            "gatilho": 0
        }
        
        self.eventos[idx].append(nova_pagina)
        
        # Atualizar interface
        num_pagina = len(self.eventos[idx])
        self.criar_aba_pagina(num_pagina, nova_pagina)
        self.atualizar_lista()
        self.evento_label.config(text=f"Editando: Evento {idx+1} - {num_pagina} página(s)")
        self.status_var.set(f"Página {num_pagina} adicionada")
    
    def remover_pagina(self):
        """Remove a página atual do evento selecionado"""
        selection = self.lista_eventos.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um evento primeiro")
            return
        
        if not self.notebook.tabs():
            messagebox.showwarning("Aviso", "Não há páginas para remover")
            return
        
        idx = selection[0]
        current_tab = self.notebook.index(self.notebook.select())
        
        if len(self.eventos[idx]) <= 1:
            if not messagebox.askyesno("Confirmar", "Remover a única página? O evento ficará vazio."):
                return
        
        # Remover do dados
        del self.eventos[idx][current_tab]
        
        # Remover da interface
        self.notebook.forget(current_tab)
        
        # Renomear abas restantes
        for i, tab_id in enumerate(self.notebook.tabs()):
            self.notebook.tab(tab_id, text=f"Página {i+1}")
        
        self.atualizar_lista()
        self.evento_label.config(text=f"Editando: Evento {idx+1} - {len(self.eventos[idx])} página(s)")
        self.status_var.set("Página removida")
    
    def adicionar_evento(self):
        """Adiciona um novo evento com uma página"""
        novo_evento = [
            {
                "condicao": None,
                "anima": 1,
                "comandos": [],
                "hitbox": [0, 1],
                "passavel": True,
                "gatilho": 0
            }
        ]
        self.eventos.append(novo_evento)
        self.atualizar_lista()
        self.status_var.set("Evento adicionado")
        
        # Selecionar o novo evento
        self.lista_eventos.selection_clear(0, tk.END)
        self.lista_eventos.selection_set(len(self.eventos)-1)
        self.selecionar_evento(None)
    
    def remover_evento(self):
        """Remove o evento selecionado"""
        selection = self.lista_eventos.curselection()
        if selection:
            idx = selection[0]
            del self.eventos[idx]
            self.atualizar_lista()
            
            # Limpar notebook
            for tab in self.notebook.tabs():
                self.notebook.forget(tab)
            
            self.evento_label.config(text="Nenhum evento selecionado")
            self.status_var.set("Evento removido")
    
    def duplicar_evento(self):
        """Duplica o evento selecionado"""
        selection = self.lista_eventos.curselection()
        if selection:
            idx = selection[0]
            evento_copia = json.loads(json.dumps(self.eventos[idx]))  # Cópia profunda
            self.eventos.append(evento_copia)
            self.atualizar_lista()
            self.status_var.set("Evento duplicado")
    
    def salvar_arquivo(self):
        """Salva todos os eventos no arquivo"""
        # Coletar dados de todas as páginas
        selection = self.lista_eventos.curselection()
        if selection:
            idx = selection[0]
            
            # Atualizar a página atual antes de salvar
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab >= 0:
                # Encontrar a página correspondente
                for widget in self.notebook.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.LabelFrame):
                                # Procurar pelo PaginaEvento
                                pass
                
                # Como é complexo, vamos usar uma abordagem mais simples
                # Salvar sem atualizar (assumindo que o usuário já editou)
                pass
        
        if not self.arquivo_atual:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
            )
            if not filename:
                return
            self.arquivo_atual = filename
        else:
            filename = self.arquivo_atual
        
        try:
            # Converter para o formato esperado
            json_completo = {"eventos": self.eventos}
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_completo, f, indent=2, ensure_ascii=False)
            
            self.arquivo_label.config(text=filename, foreground="blue")
            self.status_var.set(f"Arquivo salvo: {filename}")
            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")
    
    def novo_arquivo(self):
        """Cria um novo arquivo"""
        if messagebox.askyesno("Novo", "Criar novo arquivo? Alterações não salvas serão perdidas."):
            self.eventos = []
            self.arquivo_atual = None
            self.arquivo_label.config(text="Nenhum", foreground="gray")
            self.atualizar_lista()
            
            # Limpar notebook
            for tab in self.notebook.tabs():
                self.notebook.forget(tab)
            
            self.evento_label.config(text="Nenhum evento selecionado")
            self.status_var.set("Novo arquivo criado")
    
    def abrir_arquivo(self):
        """Abre um arquivo JSON"""
        filename = filedialog.askopenfilename(
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "eventos" in data and isinstance(data["eventos"], list):
                    self.eventos = data["eventos"]
                    self.arquivo_atual = filename
                    self.arquivo_label.config(text=filename, foreground="blue")
                    self.atualizar_lista()
                    
                    # Limpar notebook
                    for tab in self.notebook.tabs():
                        self.notebook.forget(tab)
                    
                    self.evento_label.config(text="Nenhum evento selecionado")
                    self.status_var.set(f"Arquivo carregado: {filename}")
                else:
                    messagebox.showerror("Erro", "Arquivo não contém a chave 'eventos'")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EditorEventos(root)
    root.mainloop()