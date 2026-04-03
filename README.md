### 🌿 GreenPower – Gestión de Plantas de Energía Renovable

Aplicación de escritorio en Python con Tkinter para gestionar plantas solares y renovables.  
Permite registrar plantas, subir y guardar fotos en una carpeta, visualizar miniaturas, y exportar datos a Excel o PDF.

---

✅ Características
- Registro de plantas con campos: código, nombre, tipo, potencia, etc.  
- Carga de imágenes de plantas y copia automática a la carpeta `imagenes_greenpower/plantas/`.  
- Tabla de plantas con columna de foto (nombre del archivo).  
- Miniatura de la imagen seleccionada debajo de la tabla.  
- Exportación de datos a Excel (`Plantas_exportadas.xlsx`).  
- Favicon personalizado y apariencia profesional con tema claro.

🚀 Uso
1. Asegúrate de tener Python 3.x instalado.  
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install pillow
   ```
4. Ejecuta la app:
   ```bash
   python nuevo_greenpower.py
   ```# nuevo_greenpower