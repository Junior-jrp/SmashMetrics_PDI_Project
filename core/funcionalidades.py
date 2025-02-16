import cv2
import numpy as np
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from PySide6.QtGui import QImage, QPixmap, Qt
from scipy.ndimage import distance_transform_edt
from skimage import morphology, measure, segmentation, filters, color
from scipy import ndimage as ndi


class Funcionalidades:
    def __init__(self):
        self.scale_factor = None

    def import_image(self, ui):
        file_path, _ = QFileDialog.getOpenFileName(
            ui, "Importar Imagem", "",
            "Imagens (*.png *.jpg *.bmp *.tiff)"
        )
        if file_path:
            ui.original_image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if ui.original_image is not None:
                self.display_image(ui, ui.original_image)
                ui.remove_image_button.setEnabled(True)
                QMessageBox.information(
                    ui, "Imagem Importada",
                    f"Imagem {file_path} carregada com sucesso."
                )
            else:
                QMessageBox.warning(ui, "Erro", "Falha ao carregar a imagem.")

    def remove_image(self, ui):
        ui.original_image = None
        ui.processed_image = None
        ui.image_label.clear()
        ui.image_label.setText("Nenhuma imagem carregada")
        ui.remove_image_button.setEnabled(False)
        QMessageBox.information(ui, "Remoção", "Imagem removida com sucesso.")

    def display_image(self, ui, image):
        if len(image.shape) == 2:
            height, width = image.shape
            bytes_per_line = width
            q_image = QImage(image.data, width, height,
                             bytes_per_line, QImage.Format_Grayscale8)
        else:
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height,
                             bytes_per_line, QImage.Format_BGR888)

        pixmap = QPixmap.fromImage(q_image)
        ui.image_label.setPixmap(
            pixmap.scaled(ui.image_label.size(),
                          Qt.KeepAspectRatio,
                          Qt.SmoothTransformation)
        )


    def convert_to_gray(self, ui):
        if ui.original_image is not None:
            if len(ui.original_image.shape) == 3:
                gray_image = cv2.cvtColor(ui.original_image, cv2.COLOR_BGR2GRAY)
            else:
                gray_image = ui.original_image

            gray_image = cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

            ui.processed_image = gray_image
            self.display_image(ui, gray_image)
            QMessageBox.information(
                ui, "Conversão",
                "Imagem convertida para escala de cinza 8-bit."
            )
        else:
            QMessageBox.warning(ui, "Erro", "Nenhuma imagem carregada.")

    def imposemin(img, minima):
        marker = np.full(img.shape, np.inf)
        marker[minima == 1] = 0
        mask = np.minimum(img + 1, marker)
        return morphology.reconstruction(marker, mask, method='erosion')

    def apply_watershed(self, ui):
        if ui.processed_image is not None:
            try:
                ############################################################
                # 1. carregar a imagem e converter para escala de cinza
                ############################################################
                if len(ui.processed_image.shape) == 3:
                    gray = cv2.cvtColor(ui.processed_image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = ui.processed_image.copy()
                cv2.imshow("1. Imagem em Escala de Cinza", gray)
                cv2.waitKey(0)

                ############################################################
                # 2. aplicar filtro Gaussiano (Kernel 3x3, sigma=1)
                ############################################################
                blurred = cv2.GaussianBlur(gray, (7, 7), 3)
                cv2.imshow("2. Filtro Gaussiano", blurred)
                cv2.waitKey(0)

                ############################################################
                # 3. binarização com Otsu invertida
                ############################################################
                _, binary = cv2.threshold(blurred, 0, 255,
                                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                cv2.imshow("3. Binarização Invertida", binary)
                cv2.waitKey(0)

                ############################################################
                # 4. remoção de ruído com abertura morfológica
                ############################################################
                se_disk = morphology.disk(1)
                opening_bool = morphology.opening(binary.astype(bool), se_disk)
                opening = opening_bool.astype(np.uint8) * 255
                cv2.imshow("4. Abertura Morfológica", opening)
                cv2.waitKey(0)

                ############################################################
                # 5. determinar área de fundo (sure background) por dilatação (3 iterações)
                ############################################################
                opening_uint8 = opening_bool.astype(np.uint8) * 255
                kernel_cv2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                sure_bg = cv2.dilate(opening_uint8, kernel_cv2, iterations=1)
                sure_bg = cv2.dilate(sure_bg, kernel_cv2, iterations=1)
                sure_bg = cv2.dilate(sure_bg, kernel_cv2, iterations=1)
                cv2.imshow("5. Área de Fundo (Dilatação)", sure_bg)
                cv2.waitKey(0)

                ############################################################
                # 6. Calcular a transformada de distância e definir o foreground seguro
                ############################################################
                D = ndi.distance_transform_edt(np.logical_not(opening_bool))
                dist_display = cv2.normalize(D, None, 0, 255,
                                             cv2.NORM_MINMAX).astype(np.uint8)
                cv2.imshow("6. Transformada de Distância", dist_display)
                cv2.waitKey(0)
                maxD = D.max()
                sure_fg_bool = D > 0.5 * maxD
                sure_fg = sure_fg_bool.astype(np.uint8) * 255
                cv2.imshow("7. Foreground Seguro", sure_fg)
                cv2.waitKey(0)

                ############################################################
                # 7. Determinar as regiões desconhecidas
                ############################################################
                unknown = np.logical_and(sure_bg > 0, sure_fg == 0)
                unknown_uint8 = (unknown.astype(np.uint8)) * 255
                cv2.imshow("8. Regiões Desconhecidas", unknown_uint8)
                cv2.waitKey(0)

                ############################################################
                # 8. Rotulagem dos marcadores e criação dos marcadores
                ############################################################
                markers = measure.label(sure_fg_bool, connectivity=2)
                markers = markers + 1
                markers[unknown] = 0
                markers_vis = color.label2rgb(markers, bg_label=0, bg_color=(1, 1, 1))
                markers_vis = (markers_vis * 255).astype(np.uint8)
                cv2.imshow("9. Marcadores (Markers)", markers_vis)
                cv2.waitKey(0)

                ############################################################
                # 9. Calcular o gradiente da imagem
                ############################################################
                gradmag = filters.sobel(gray.astype(float) / 255)
                grad_norm = cv2.normalize(gradmag, None, 0, 255,
                                          cv2.NORM_MINMAX).astype(np.uint8)
                cv2.imshow("10. Gradiente da Imagem", grad_norm)
                cv2.waitKey(0)

                ############################################################
                # Passo 10: Impor mínimos e aplicar o Watershed
                ############################################################
                minima = (markers > 0).astype(np.uint8)
                markers_imposed = Funcionalidades.imposemin(gradmag, minima)
                L_ws = segmentation.watershed(
                    markers_imposed,
                    connectivity=2,
                    watershed_line=False
                )

                L_ws_vis = color.label2rgb(L_ws, bg_label=0, bg_color=(1, 1, 1))
                L_ws_vis = (L_ws_vis * 255).astype(np.uint8)

                cv2.imshow("Segmentação via Watershed", L_ws_vis)
                cv2.waitKey(0)

                ############################################################
                # Passo 11: Encontrar bordas da segmentação
                ############################################################
                boundary = morphology.dilation(L_ws) != morphology.erosion(L_ws)

                ############################################################
                # Passo 12: Sobrepor bordas na imagem original
                ############################################################
                if len(ui.original_image.shape) == 2:
                    I_color = cv2.cvtColor(ui.original_image, cv2.COLOR_GRAY2BGR)
                else:
                    I_color = ui.original_image.copy()

                I_overlay = I_color.copy()
                I_overlay[boundary] = [0, 0, 255]

                cv2.imshow("12. Segmentação por Watershed (Overlay)", I_overlay)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

                ############################################################
                # Atualizar a interface com a imagem segmentada
                ############################################################
                ui.processed_image = I_overlay
                self.display_image(ui, I_overlay)

                QMessageBox.information(ui, "Watershed",
                                        "Segmentação concluída com:\n"
                                        "- Contornos em vermelho")
            except Exception as e:
                QMessageBox.critical(ui, "Erro", f"Erro no processamento:\n{str(e)}")
        else:
            QMessageBox.warning(ui, "Erro", "Nenhuma imagem processada.")

    @staticmethod
    def calibrate_image(ui):
        if ui.original_image is not None:
            image_copy = ui.original_image.copy()
            scale_factors = []

            for i in range(3):
                QMessageBox.information(ui, "Calibração", f"Selecione os pontos para a calibração {i + 1}/3.")

                points = Funcionalidades.select_points(image_copy)
                if len(points) != 2:
                    QMessageBox.warning(ui, "Erro", "Selecione exatamente dois pontos.")
                    return

                pixel_distance = Funcionalidades.calculate_pixel_distance(points[0], points[1])
                if pixel_distance == 0:
                    QMessageBox.warning(ui, "Erro", "A distância entre os pontos não pode ser zero.")
                    return

                real_distance, ok = QInputDialog.getDouble(
                    ui, "Calibração",
                    f"Insira a distância real para a calibração {i + 1}/3 (em cm):",
                    decimals=2
                )
                if not ok or real_distance <= 0:
                    QMessageBox.warning(ui, "Erro", "Distância real inválida ou não fornecida.")
                    return

                scale_factor = real_distance / pixel_distance
                scale_factors.append(scale_factor)

            ui.scale_factor = np.mean(scale_factors)

            QMessageBox.information(
                ui, "Calibração",
                f"Escala calibrada com sucesso!\n"
                f"Fator médio: {ui.scale_factor:.4f} cm/px\n"
                f"(Baseado em 3 medições)"
            )
        else:
            QMessageBox.warning(ui, "Erro", "Nenhuma imagem carregada para calibrar.")

    @staticmethod
    def select_points(image):
        points = []
        zoom_scale = 3
        zoom_size = 100

        draw_image = image.copy()
        zoom_window = None

        def click_event(event, x, y, flags, param):
            nonlocal draw_image, zoom_window
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(points) == 0:
                    points.append((x, y))
                    cv2.circle(draw_image, (x, y), 5, (0, 255, 0), -1)
                    cv2.imshow("Seleção de Pontos", draw_image)
                elif len(points) == 1:
                    points.append((x, y))
                    cv2.line(draw_image, points[0], points[1], (0, 255, 0), 2)
                    cv2.imshow("Seleção de Pontos", draw_image)
            elif event == cv2.EVENT_MOUSEMOVE:
                x_start = max(x - zoom_size // 2, 0)
                y_start = max(y - zoom_size // 2, 0)
                x_end = min(x + zoom_size // 2, image.shape[1])
                y_end = min(y + zoom_size // 2, image.shape[0])
                zoom_region = image[y_start:y_end, x_start:x_end].copy()
                cv2.circle(zoom_region, (zoom_size // 2, zoom_size // 2), 3, (0, 0, 255), -1)
                zoom_resized = cv2.resize(zoom_region, (zoom_size * zoom_scale, zoom_size * zoom_scale),
                                          interpolation=cv2.INTER_LINEAR)
                cv2.imshow("Zoom", zoom_resized)
                if len(points) == 1:
                    temp_image = draw_image.copy()
                    cv2.line(temp_image, points[0], (x, y), (255, 0, 0), 1)
                    cv2.imshow("Seleção de Pontos", temp_image)

        cv2.imshow("Seleção de Pontos", draw_image)
        cv2.setMouseCallback("Seleção de Pontos", click_event)

        while len(points) < 2:
            if cv2.waitKey(100) == 27:
                break

        cv2.destroyWindow("Zoom")
        cv2.destroyWindow("Seleção de Pontos")
        return points

        while len(points) < 2:
            if cv2.waitKey(100) == 27:
                break

        cv2.destroyAllWindows()
        return points

    @staticmethod
    def calculate_pixel_distance(point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    @staticmethod
    def calculate_pixel_distance(point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def measure_deformation(self, ui):
        image_copy = ui.processed_image.copy()
        points = Funcionalidades.select_points(image_copy)
        if len(points) != 2:
            QMessageBox.warning(ui, "Erro", "Selecione exatamente dois pontos para medir a deformação.")
            return None

        pixel_distance = Funcionalidades.calculate_pixel_distance(points[0], points[1])
        if ui.scale_factor is None:
            QMessageBox.warning(ui, "Erro", "Calibre a imagem primeiro!")
            return None

        real_distance = pixel_distance * ui.scale_factor
        QMessageBox.information(ui, "Medição de Deformação",
                                f"Deformação medida: {real_distance:.2f} cm")
        return real_distance

    def calculate_energy_and_velocity(self, ui, deformation_cm):
        mass, ok_mass = QInputDialog.getDouble(ui, "Massa", "Insira a massa do veículo (kg):", decimals=2)
        if not ok_mass or mass <= 0:
            QMessageBox.warning(ui, "Erro", "Massa inválida.")
            return
        deformation_m = deformation_cm / 100.0
        F_eff = 2.621e6
        Edef = F_eff * (deformation_m ** 2)

        velocity = np.sqrt((2 * Edef) / mass)
        velocity_kmh = velocity * 3.6

        report_content = (
            f"**Resultados da Análise (Método Ajustado)**\n"
            f"- Deformação medida: {deformation_cm:.2f} cm\n"
            f"- Energia de deformação (Edef): {Edef:.2f} N.m\n"
            f"- Velocidade estimada: {velocity_kmh:.2f} km/h\n"
        )
        ui.report_text.setPlainText(report_content)
        return velocity_kmh

    def handle_velocity_calculation(self, ui):
        deformation = self.measure_deformation(ui)

        if deformation is not None:
            self.calculate_energy_and_velocity(ui, deformation)
        else:
            QMessageBox.warning(ui, "Erro", "Não foi possível medir a deformação. Selecione dois pontos corretamente.")
