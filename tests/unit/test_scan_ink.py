"""Testes da separação entre tinta (caneta azul) e guias ciano do modelo."""
import cv2
import numpy as np

from petricor.scan.ink import InkExtractor, InkThresholds


class TestInkExtractor:
    """Cores reais medidas nas folhas (BGR, formato do OpenCV)."""

    INK_BGR = (163, 113, 101)
    CYAN_BGR = (235, 215, 140)

    @staticmethod
    def blank(h=200, w=200):
        return np.full((h, w, 3), 252, np.uint8)

    def test_tinta_azul_vira_mascara_e_guia_ciano_nao(self):
        img = self.blank()
        cv2.line(img, (10, 150), (190, 150), self.CYAN_BGR, 3)
        cv2.line(img, (100, 20), (100, 180), self.INK_BGR, 5)
        mask = InkExtractor().extract(img)
        assert mask[100, 100]
        assert not mask[150, 30]
        assert not mask[50, 30]

    def test_traco_cruzando_a_guia_continua_inteiro(self):
        img = self.blank()
        cv2.line(img, (100, 20), (100, 180), self.INK_BGR, 5)
        cv2.line(img, (10, 150), (190, 150), self.CYAN_BGR, 3)  # guia por cima
        mask = InkExtractor().extract(img)
        assert mask[145:156, 100].all()

    def test_ruido_pequeno_e_removido(self):
        img = self.blank()
        cv2.circle(img, (50, 50), 1, self.INK_BGR, -1)
        mask = InkExtractor(InkThresholds(min_area=20)).extract(img)
        assert not mask.any()
