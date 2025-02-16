from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QStackedWidget, QTextEdit, QComboBox, QInputDialog
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core.funcionalidades import Funcionalidades


class SmashMetricsUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.funcionalidades = Funcionalidades()
        self.setWindowTitle("SmashMetrics - Análise Forense de Colisões")
        self.setGeometry(100, 100, 1200, 800)

        self.original_image = None
        self.processed_image = None
        self.scale_factor = None
        self.selected_stiffness = None

        self.setup_ui()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addLayout(self.create_navbar())
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        self.setup_screens()

    def create_navbar(self):
        navbar = QHBoxLayout()
        navbar.setSpacing(10)
        navbar.setContentsMargins(10, 10, 10, 10)

        buttons = [
            ("⌂ Início", self.show_dashboard),
            ("\U0001F4F7 Análise", self.show_analysis),
            ("\U0001F4C8 Relatório", self.show_report),
            ("\U0001F4DD Sobre", self.show_about),
        ]

        for label, handler in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px;
                    font-size: 14px;
                    background-color: #2c3e50;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
            """)
            btn.clicked.connect(handler)
            navbar.addWidget(btn)

        return navbar

    def setup_screens(self):
        self.dashboard_widget = self.create_dashboard_screen()
        self.stacked_widget.addWidget(self.dashboard_widget)

        self.analysis_widget = self.create_analysis_screen()
        self.stacked_widget.addWidget(self.analysis_widget)

        self.report_widget = self.create_report_screen()
        self.stacked_widget.addWidget(self.report_widget)

        self.about_widget = self.create_about_screen()
        self.stacked_widget.addWidget(self.about_widget)

        self.stacked_widget.setCurrentWidget(self.dashboard_widget)

    @staticmethod
    def create_dashboard_screen():
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(20)

        title = QLabel("SmashMetrics")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 42px;
            font-weight: bold;
            color: #3498db;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Sistema de análise forense de colisões veiculares")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 20px; color: #ecf0f1; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        icon_label = QLabel()
        icon_pixmap = QPixmap("logo_smashmetrics-removebg-preview.png").scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        description = QLabel(
            "Este software foi desenvolvido como parte do projeto da disciplina de Processamento Digital de Imagens no IFCE - Campus Maracanaú. "
            "O SmashMetrics permite analisar imagens de colisões veiculares e estimar deformações e velocidades usando métodos forenses."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 16px; color: #bdc3c7; line-height: 1.5;")
        layout.addWidget(description)

        return widget

    def create_analysis_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Análise de Imagem de Colisão")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; color: #ecf0f1; font-weight: bold;")
        layout.addWidget(title)

        self.image_label = QLabel("Nenhuma imagem carregada")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #2c3e50; border: 2px dashed #7f8c8d; min-height: 500px; margin-top: 10px;"
        )
        layout.addWidget(self.image_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # Botões já existentes
        buttons = [
            ("Importar Imagem", self.funcionalidades.import_image),
            ("Converter para 8-bit", self.funcionalidades.convert_to_gray),
            ("Segmentar Deformação", self.funcionalidades.apply_watershed),
            ("Calibrar Escala", self.funcionalidades.calibrate_image),
            ("Calcular Velocidade", self.funcionalidades.handle_velocity_calculation),
        ]

        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("padding: 10px 20px; font-size: 16px;")
            btn.clicked.connect(lambda _, h=handler: h(self))
            button_layout.addWidget(btn)

            # Adiciona o botão de remover imagem
        self.remove_image_button = QPushButton("Remover Imagem")
        self.remove_image_button.setStyleSheet("padding: 10px 20px; font-size: 16px;")
        self.remove_image_button.clicked.connect(self.remove_image)
        button_layout.addWidget(self.remove_image_button)

        # ComboBox para seleção de rigidez
        self.stiffness_combo = QComboBox()
        self.stiffness_combo.addItems([
            "Carro Sedan (k=150000 N/m)",
            "Caminhonete (k=250000 N/m)",
            "Personalizado..."
        ])
        self.stiffness_combo.setStyleSheet("padding: 10px; font-size: 16px;")
        self.stiffness_combo.currentIndexChanged.connect(self.update_stiffness_value)
        button_layout.addWidget(self.stiffness_combo)

        layout.addLayout(button_layout)
        return widget

    def create_report_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QLabel("Relatório de Análise")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 30px; font-weight: bold; color: #ecf0f1; margin-bottom: 20px;")
        layout.addWidget(header)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("""
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 2px solid #34495e;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 16px;
        """)
        layout.addWidget(self.report_text)

        btn_export = QPushButton("Exportar para PDF")
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #1e8449;
            }
        """)
        layout.addWidget(btn_export, alignment=Qt.AlignRight)
        return widget

    def create_about_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QLabel("Sobre o SmashMetrics")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 30px; font-weight: bold; color: #ecf0f1; margin-bottom: 20px;")
        layout.addWidget(header)

        content = QLabel(
            "SmashMetrics é um sistema de análise forense de colisões veiculares desenvolvido "
            "para auxiliar na reconstituição de acidentes de trânsito por meio de técnicas avançadas de "
            "Processamento Digital de Imagens (PDI).\n\n"
            "A ferramenta permite a medição de deformações em veículos a partir de imagens, aplicando "
            "metodologias consagradas como a de Campbell, para estimar a energia de impacto e a velocidade da colisão.\n\n"
            "Este software faz parte de um projeto acadêmico desenvolvido como requisito para a disciplina de "
            "Processamento Digital de Imagens, no Instituto Federal de Educação, Ciência e Tecnologia do Ceará (IFCE) – Campus Maracanaú.\n\n"
            "O SmashMetrics é voltado para peritos, pesquisadores e profissionais da área forense que buscam uma "
            "solução de baixo custo e acessível para análise e reconstrução de sinistros. O projeto tem caráter educacional e experimental, "
            "visando aprimorar a aplicação de visão computacional na investigação de acidentes.\n\n"
            "Para mais informações, visite nosso repositório no GitHub ou entre em contato com nossa equipe.\n\n"
            "Versão 1.0"
        )

        content.setStyleSheet("font-size: 18px; color: #bdc3c7; line-height: 1.5;")
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignJustify)
        layout.addWidget(content)

        logo = QLabel()
        logo_pixmap = QPixmap("path/to/your/logo.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(logo_pixmap)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        return widget

    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_widget)

    def show_analysis(self):
        self.stacked_widget.setCurrentWidget(self.analysis_widget)

    def show_report(self):
        self.stacked_widget.setCurrentWidget(self.report_widget)

    def show_about(self):
        self.stacked_widget.setCurrentWidget(self.about_widget)

    def remove_image(self):
        self.original_image = None
        self.processed_image = None
        self.image_label.clear()
        self.image_label.setText("Nenhuma imagem carregada")
        self.remove_image_button.setEnabled(False)

    def update_stiffness_value(self):
        """Atualiza o valor de rigidez com base na seleção do usuário."""
        selection = self.stiffness_combo.currentText()
        if "Sedan" in selection:
            self.selected_stiffness = 150000  # exemplo para Sedan
        elif "Caminhonete" in selection:
            self.selected_stiffness = 250000  # exemplo para Caminhonete
        else:
            value, ok = QInputDialog.getDouble(self, "Rigidez Personalizada",
                                               "Insira o valor da constante de rigidez (N/m):", decimals=2)
            self.selected_stiffness = value if ok else None

    def handle_calculate_velocity(self):
        deformation = self.funcionalidades.measure_deformation(self)
        if deformation is None:
            return
        if self.selected_stiffness is None:
            self.update_stiffness_value()
            self.funcionalidades.calculate_energy_and_velocity_campbell(self)

