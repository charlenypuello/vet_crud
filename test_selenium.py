import os
import time
import unittest
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ========================================================
# CONFIGURACIÓN DE CARPETAS PARA REPORTES Y CAPTURAS
# ========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
SCREEN_DIR = os.path.join(BASE_DIR, "screenshots")

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(SCREEN_DIR, exist_ok=True)


# ========================================================
# CLASE DE PRUEBAS SELENIUM
# ========================================================

class VetCrudTests(unittest.TestCase):
    """
    Pruebas automatizadas para la app CRUD Veterinaria.
    """

    def setUp(self):
        """Se ejecuta ANTES de cada prueba."""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # Si quieres que no abra ventana, puedes probar:
        # options.add_argument("--headless=new")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.implicitly_wait(5)
        self.base_url = "http://127.0.0.1:5000"

    def tearDown(self):
        """Se ejecuta DESPUÉS de cada prueba."""
        self.driver.quit()

    # ==========================
    # Funciones auxiliares
    # ==========================

    def login(self, username="admin", password="1234"):
        """Inicia sesión en la app."""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def save_screenshot(self, name: str):
        """Guarda captura en /screenshots."""
        ruta = os.path.join(SCREEN_DIR, name)
        self.driver.save_screenshot(ruta)

    # ==========================
    # PRUEBAS
    # ==========================

    def test_01_login_exitoso_camino_feliz(self):
        """Camino feliz: login correcto."""
        self.login("admin", "1234")
        time.sleep(1)
        self.assertIn("Lista de Pacientes", self.driver.page_source)
        self.save_screenshot("01_login_exitoso.png")

    def test_02_login_fallido_negativo(self):
        """Prueba negativa: login con contraseña incorrecta."""
        self.login("admin", "clave_incorrecta")
        time.sleep(1)
        self.assertIn("Usuario o contraseña incorrectos", self.driver.page_source)
        self.save_screenshot("02_login_invalido.png")

    def test_03_crear_paciente_camino_feliz(self):
        """Camino feliz: crear paciente con datos válidos."""
        self.login()
        time.sleep(1)

        self.driver.find_element(By.LINK_TEXT, "Crear nuevo paciente").click()
        self.driver.find_element(By.NAME, "nombre").send_keys("Firulais")
        self.driver.find_element(By.NAME, "especie").send_keys("Perro")
        self.driver.find_element(By.NAME, "dueno").send_keys("Juan Pérez")
        self.driver.find_element(By.NAME, "telefono").send_keys("8091234567")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        self.assertIn("Paciente creado correctamente", self.driver.page_source)
        self.assertIn("Firulais", self.driver.page_source)
        self.save_screenshot("03_crear_paciente_ok.png")

    def test_04_crear_paciente_campos_obligatorios_limite(self):
        """Prueba de límites: dejar nombre vacío."""
        self.login()
        time.sleep(1)

        self.driver.find_element(By.LINK_TEXT, "Crear nuevo paciente").click()
        self.driver.find_element(By.NAME, "nombre").send_keys("")  # vacío
        self.driver.find_element(By.NAME, "especie").send_keys("Gato")
        self.driver.find_element(By.NAME, "dueno").send_keys("Ana Gómez")
        self.driver.find_element(By.NAME, "telefono").send_keys("8095550000")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        self.assertIn("Nombre, especie y dueño son obligatorios", self.driver.page_source)
        self.save_screenshot("04_crear_paciente_faltan_campos.png")

    def test_05_editar_paciente(self):
        """Editar el primer paciente de la lista (si existe)."""
        self.login()
        time.sleep(1)

        enlaces_editar = self.driver.find_elements(By.LINK_TEXT, "Editar")
        if not enlaces_editar:
            self.skipTest("No hay pacientes para editar")

        enlaces_editar[0].click()
        time.sleep(1)

        telefono_input = self.driver.find_element(By.NAME, "telefono")
        telefono_input.clear()
        telefono_input.send_keys("8099999999")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        self.assertIn("Paciente actualizado correctamente", self.driver.page_source)
        self.save_screenshot("05_editar_paciente.png")

    def test_06_eliminar_paciente(self):
        """Eliminar el primer paciente de la lista (si existe)."""
        self.login()
        time.sleep(1)

        filas = self.driver.find_elements(By.CSS_SELECTOR, "table tr")[1:]
        if not filas:
            self.skipTest("No hay pacientes para eliminar")

        cant_antes = len(filas)
        botones_eliminar = self.driver.find_elements(
            By.XPATH, "//form/button[contains(text(),'Eliminar')]"
        )
        if not botones_eliminar:
            self.skipTest("No se encontró botón de eliminar")

        botones_eliminar[0].click()
        time.sleep(1)

        try:
            alerta = self.driver.switch_to.alert
            alerta.accept()
            time.sleep(1)
        except Exception:
            pass

        filas_despues = self.driver.find_elements(By.CSS_SELECTOR, "table tr")[1:]
        cant_despues = len(filas_despues)

        self.assertLess(cant_despues, cant_antes)
        self.save_screenshot("06_eliminar_paciente.png")


# ========================================================
# EJECUCIÓN Y REPORTE HTML
# ========================================================

if __name__ == "__main__":
    # Ejecutar pruebas
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(VetCrudTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Datos para el reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"reporte_pruebas_{timestamp}.html")

    # Preparar estructura de resultados
    case_names = unittest.defaultTestLoader.getTestCaseNames(VetCrudTests)
    test_ids = [
        f"{VetCrudTests.__module__}.{VetCrudTests.__name__}.{name}"
        for name in case_names
    ]

    status = {tid: "OK" for tid in test_ids}
    details = {tid: "" for tid in test_ids}

    for test, tb in result.failures:
        tid = test.id()
        status[tid] = "FAIL"
        details[tid] = tb

    for test, tb in result.errors:
        tid = test.id()
        status[tid] = "ERROR"
        details[tid] = tb

    for test, reason in getattr(result, "skipped", []):
        tid = test.id()
        status[tid] = "SKIPPED"
        details[tid] = reason

    # Crear HTML
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'>")
        f.write("<title>Reporte de Pruebas Vet CRUD</title></head><body>")
        f.write("<h1>Reporte de Pruebas - Clínica Veterinaria CRUD</h1>")
        f.write(f"<p>Fecha y hora de ejecución: {datetime.now()}</p>")
        f.write(f"<p>Total: {result.testsRun} | Fallidas: {len(result.failures)} "
                f"| Errores: {len(result.errors)} | Omitidas: {len(getattr(result, 'skipped', []))}</p>")
        f.write("<hr>")
        f.write("<table border='1' cellpadding='5' cellspacing='0'>")
        f.write("<tr><th>Prueba</th><th>Estado</th><th>Detalle</th></tr>")

        for tid in test_ids:
            st = status.get(tid, "NO EJECUTADA")
            det = details.get(tid, "")
            if st == "FAIL":
                color = "#ffcccc"
            elif st == "ERROR":
                color = "#ffe0cc"
            elif st == "SKIPPED":
                color = "#eeeeee"
            else:
                color = "#ccffcc"

            f.write(f"<tr style='background-color:{color}'>")
            f.write(f"<td>{tid}</td>")
            f.write(f"<td>{st}</td>")
            f.write(f"<td><pre>{det}</pre></td>")
            f.write("</tr>")

        f.write("</table>")
        f.write("<p>Capturas de pantalla en la carpeta <b>screenshots</b>.</p>")
        f.write("</body></html>")

    print(f"\nReporte HTML generado en: {report_path}")
