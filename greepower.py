"""
GreenPower - Gestión Energía Renovable
Script unificado con integración MySQL
Requiere: pip install mysql-connector-python
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
import json

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN BASE DE DATOS
# ══════════════════════════════════════════════════════════════════
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",          # ← Cambia por tu contraseña de MySQL
    "database": "greenpower",
    "port":     3306,
}

try:
    import mysql.connector
    MYSQL_DISPONIBLE = True
except ImportError:
    MYSQL_DISPONIBLE = False


# ══════════════════════════════════════════════════════════════════
# CAPA DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.conn   = None
        self.cursor = None
        self.conectado = False

    def conectar(self) -> bool:
        if not MYSQL_DISPONIBLE:
            return False
        try:
            self.conn   = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            self.conectado = True
            return True
        except Exception:
            self.conectado = False
            return False

    def desconectar(self):
        try:
            if self.cursor: self.cursor.close()
            if self.conn:   self.conn.close()
        except Exception:
            pass
        self.conectado = False

    def ejecutar(self, query: str, params=None) -> bool:
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def consultar(self, query: str, params=None) -> List[Dict]:
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            raise e

    def consultar_uno(self, query: str, params=None) -> Optional[Dict]:
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Exception as e:
            raise e


db = Database()

# Listas en memoria para modo offline
plantas_mem:   List[Dict] = []
equipos_mem:   List[Dict] = []
estaciones_mem: List[Dict] = []


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _float(v) -> float:
    try:   return float(v or 0)
    except: return 0.0

def _int(v) -> int:
    try:   return int(float(v or 0))
    except: return 0

def _lat(coords: str) -> Optional[float]:
    try:   return float(coords.split(',')[0].strip())
    except: return None

def _lon(coords: str) -> Optional[float]:
    try:   return float(coords.split(',')[1].strip())
    except: return None


# ══════════════════════════════════════════════════════════════════
# CRUD — PLANTAS
# ══════════════════════════════════════════════════════════════════

def agregar_planta(data: Dict[str, Any]) -> bool:
    codigo = data.get('codigo_planta', '').strip()
    if not codigo:
        return False
    if db.conectado:
        if db.consultar_uno("SELECT 1 FROM plantas WHERE codigo_planta=%s", (codigo,)):
            return False
        db.ejecutar("""
            INSERT INTO plantas
              (codigo_planta,nombre,tipo,ubicacion,latitud,longitud,
               extension_hectareas,capacidad_mw,fecha_puesta_marcha,
               inversion_inicial,vida_util_anios,estado_operativo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            codigo,
            data.get('nombre_planta',''),
            data.get('tipo_planta','solar_fotovoltaica'),
            data.get('ubicacion_planta',''),
            _lat(data.get('coordenadas_planta','')),
            _lon(data.get('coordenadas_planta','')),
            _float(data.get('extension_planta')),
            _float(data.get('capacidad_planta')),
            data.get('fecha_marcha_planta') or None,
            _float(data.get('inversion_planta')),
            _int(data.get('vida_util_planta')),
            'operativa',
        ))
        return True
    else:
        if any(p['codigo_planta'] == codigo for p in plantas_mem):
            return False
        plantas_mem.append({
            'codigo_planta': codigo, 'nombre': data.get('nombre_planta',''),
            'tipo': data.get('tipo_planta',''), 'ubicacion': data.get('ubicacion_planta',''),
            'capacidad_mw': _float(data.get('capacidad_planta')), 'estado_operativo': 'operativa',
        })
        return True


def obtener_plantas() -> List[Dict]:
    if db.conectado:
        return db.consultar(
            "SELECT codigo_planta,nombre,tipo,capacidad_mw,estado_operativo FROM plantas ORDER BY nombre")
    return plantas_mem


def eliminar_planta(codigo: str) -> bool:
    if db.conectado:
        db.ejecutar("DELETE FROM plantas WHERE codigo_planta=%s", (codigo,))
    else:
        plantas_mem[:] = [p for p in plantas_mem if p['codigo_planta'] != codigo]
    return True


# ══════════════════════════════════════════════════════════════════
# CRUD — EQUIPOS
# ══════════════════════════════════════════════════════════════════

def agregar_equipo(data: Dict[str, Any]) -> bool:
    n_serie = data.get('n_serie_equipo', '').strip()
    if not n_serie:
        return False
    if db.conectado:
        if db.consultar_uno("SELECT 1 FROM equipos WHERE numero_serie=%s", (n_serie,)):
            return False
        db.ejecutar("""
            INSERT INTO equipos
              (numero_serie,tipo_especifico,marca,modelo,
               potencia_nominal_mw,eficiencia,estado_actual,codigo_planta)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            n_serie,
            data.get('tipo_equipo',''),
            data.get('marca_equipo',''),
            data.get('modelo_equipo',''),
            _float(data.get('potencia_equipo')),
            _float(data.get('eficiencia_equipo')),
            'operativo',
            data.get('codigo_planta') or None,
        ))
        return True
    else:
        if any(e['numero_serie'] == n_serie for e in equipos_mem):
            return False
        equipos_mem.append({
            'numero_serie': n_serie, 'tipo_especifico': data.get('tipo_equipo',''),
            'marca': data.get('marca_equipo',''),
            'potencia_nominal_mw': _float(data.get('potencia_equipo')), 'estado_actual': 'operativo',
        })
        return True


def obtener_equipos() -> List[Dict]:
    if db.conectado:
        return db.consultar(
            "SELECT numero_serie,tipo_especifico,marca,potencia_nominal_mw,estado_actual FROM equipos ORDER BY numero_serie")
    return equipos_mem


def eliminar_equipo(n_serie: str) -> bool:
    if db.conectado:
        db.ejecutar("DELETE FROM equipos WHERE numero_serie=%s", (n_serie,))
    else:
        equipos_mem[:] = [e for e in equipos_mem if e['numero_serie'] != n_serie]
    return True


# ══════════════════════════════════════════════════════════════════
# CRUD — ESTACIONES
# ══════════════════════════════════════════════════════════════════

def agregar_estacion(data: Dict[str, Any]) -> bool:
    codigo = data.get('codigo_estacion', '').strip()
    if not codigo:
        return False
    if db.conectado:
        if db.consultar_uno(
                "SELECT 1 FROM estaciones_meteorologicas WHERE codigo_estacion=%s", (codigo,)):
            return False
        eq_raw = data.get('equipos_estacion', '')
        eq_json = json.dumps([x.strip() for x in eq_raw.split(',') if x.strip()])
        db.ejecutar("""
            INSERT INTO estaciones_meteorologicas
              (codigo_estacion,ubicacion,latitud,longitud,
               equipos_instalados,frecuencia_lectura,estado_funcionamiento)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            codigo,
            data.get('ubicacion_estacion',''),
            _lat(data.get('coordenadas_estacion','')),
            _lon(data.get('coordenadas_estacion','')),
            eq_json,
            data.get('frecuencia_estacion',''),
            'operativa',
        ))
        return True
    else:
        if any(e['codigo_estacion'] == codigo for e in estaciones_mem):
            return False
        estaciones_mem.append({
            'codigo_estacion': codigo, 'ubicacion': data.get('ubicacion_estacion',''),
            'equipos_instalados': data.get('equipos_estacion',''), 'estado_funcionamiento': 'operativa',
        })
        return True


def obtener_estaciones() -> List[Dict]:
    if db.conectado:
        return db.consultar(
            "SELECT codigo_estacion,ubicacion,equipos_instalados,estado_funcionamiento FROM estaciones_meteorologicas ORDER BY codigo_estacion")
    return estaciones_mem


# ══════════════════════════════════════════════════════════════════
# LECTURA DE DATOS AVANZADOS (vistas + stored procedures)
# ══════════════════════════════════════════════════════════════════

def obtener_metricas() -> Dict:
    if db.conectado:
        try:
            c = db.conn.cursor()
            c.execute("CALL sp_dashboard_general(@p,@h,@i,@m)")
            c.execute("SELECT @p,@h,@i,@m")
            row = c.fetchone()
            c.close()
            if row:
                return {'plantas_operativas': row[0] or 0, 'produccion_hoy': float(row[1] or 0),
                        'incidencias_abiertas': row[2] or 0, 'energia_mes': float(row[3] or 0)}
        except Exception:
            pass
        # Fallback queries directas
        try:
            def n(q): return (db.consultar_uno(q) or {}).get('n', 0)
            return {
                'plantas_operativas':  n("SELECT COUNT(*) AS n FROM plantas WHERE estado_operativo='operativa'"),
                'produccion_hoy':      float(n("SELECT COALESCE(SUM(energia_generada_mwh),0) AS n FROM produccion_energetica WHERE DATE(fecha_hora)=CURDATE()")),
                'incidencias_abiertas':n("SELECT COUNT(*) AS n FROM incidencias WHERE estado='abierta'"),
                'energia_mes':         float(n("SELECT COALESCE(SUM(energia_generada_mwh),0) AS n FROM produccion_energetica WHERE MONTH(fecha_hora)=MONTH(CURDATE())")),
            }
        except Exception:
            pass
    return {'plantas_operativas': len(plantas_mem), 'produccion_hoy': 0,
            'incidencias_abiertas': 0, 'energia_mes': 0}


def obtener_produccion_reciente() -> List[Dict]:
    if db.conectado:
        try:
            return db.consultar("""
                SELECT p.nombre AS planta, pe.potencia_instantanea_mw,
                       pe.energia_generada_mwh, pe.factor_capacidad, pe.fecha_hora
                FROM produccion_energetica pe
                JOIN plantas p ON pe.codigo_planta=p.codigo_planta
                ORDER BY pe.fecha_hora DESC LIMIT 20
            """)
        except Exception:
            pass
    return []


def obtener_incidencias() -> List[Dict]:
    if db.conectado:
        try:
            return db.consultar("""
                SELECT i.codigo_incidencia, p.nombre AS planta, i.tipo_incidencia,
                       i.descripcion, i.impacto_produccion, i.estado, i.fecha_hora
                FROM incidencias i
                JOIN plantas p ON i.codigo_planta=p.codigo_planta
                ORDER BY i.fecha_hora DESC LIMIT 30
            """)
        except Exception:
            pass
    return []


def obtener_mantenimientos() -> List[Dict]:
    if db.conectado:
        try:
            return db.consultar("""
                SELECT m.orden_trabajo, p.nombre AS planta, m.tipo_mantenimiento,
                       m.descripcion_actividades, m.fecha_programada, m.estado
                FROM mantenimientos m
                JOIN plantas p ON m.codigo_planta=p.codigo_planta
                ORDER BY m.fecha_programada DESC LIMIT 30
            """)
        except Exception:
            pass
    return []


# ══════════════════════════════════════════════════════════════════
# GUI
# ══════════════════════════════════════════════════════════════════

class GreenPowerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌿 GreenPower - Gestión Energía Renovable")
        self.root.geometry("960x720")
        self.root.minsize(800, 600)

        self._conectar_db()
        self.crear_menu()
        self.crear_barra_estado()
        self.crear_pestanas()

    # ── CONEXIÓN ──────────────────────────────────────────────────
    def _conectar_db(self):
        if not MYSQL_DISPONIBLE:
            self._msg_estado = "⚠️ Instala mysql-connector-python — modo offline"
        elif db.conectar():
            self._msg_estado = f"✅ Conectado a MySQL  ·  {DB_CONFIG['host']}:{DB_CONFIG['port']}  /  {DB_CONFIG['database']}"
        else:
            self._msg_estado = "⚠️ Sin conexión a MySQL — modo offline (datos en memoria)"

    def crear_barra_estado(self):
        color = "#27ae60" if db.conectado else "#e67e22"
        self.barra = tk.Label(self.root, text=self._msg_estado,
                              bg=color, fg="white", anchor='w', padx=12, pady=4,
                              font=('Arial', 9))
        self.barra.pack(fill='x', side='bottom')

    # ── MENÚ ──────────────────────────────────────────────────────
    def crear_menu(self):
        mb = tk.Menu(self.root)
        self.root.config(menu=mb)

        arch = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="📁 Archivo", menu=arch)
        arch.add_command(label="🔌 Reconectar BD",        command=self._reconectar)
        arch.add_command(label="⚙️ Configurar conexión",  command=self._config_db)
        arch.add_separator()
        arch.add_command(label="❌ Salir",                command=self.root.quit)

        dat = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="🗄️ Datos", menu=dat)
        dat.add_command(label="🔄 Recargar todo", command=self._recargar_todo)

    # ── PESTAÑAS ──────────────────────────────────────────────────
    def crear_pestanas(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand=True, padx=10, pady=(10, 0))

        self._tab_plantas()
        self._tab_equipos()
        self._tab_estaciones()
        self._tab_produccion()
        self._tab_incidencias()
        self._tab_mantenimientos()

    # ══════════════════════════════════════════════════════════════
    # HELPER: construye formulario en 2 columnas
    # ══════════════════════════════════════════════════════════════
    def _form(self, parent, campos_izq, campos_der, store: dict, combos: dict = None):
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)
        combos = combos or {}
        for row, (lbl, key) in enumerate(campos_izq):
            ttk.Label(parent, text=lbl).grid(row=row, column=0, sticky='w', pady=2, padx=(0,6))
            w = ttk.Entry(parent, width=22)
            w.grid(row=row, column=1, sticky='ew', pady=2)
            store[key] = w
        for row, (lbl, key) in enumerate(campos_der):
            ttk.Label(parent, text=lbl).grid(row=row, column=2, sticky='w', pady=2, padx=(12,6))
            if key in combos:
                w = ttk.Combobox(parent, width=20, state='readonly', values=combos[key])
                w.set(combos[key][0])
            else:
                w = ttk.Entry(parent, width=22)
            w.grid(row=row, column=3, sticky='ew', pady=2)
            store[key] = w

    def _tabla(self, parent, cols, widths, height=10):
        t = ttk.Treeview(parent, columns=cols, show='headings', height=height)
        for col, w in zip(cols, widths):
            t.heading(col, text=col)
            t.column(col, width=w)
        sb = ttk.Scrollbar(parent, orient='vertical', command=t.yview)
        t.configure(yscroll=sb.set)
        t.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        return t

    def _limpiar(self, store: dict):
        for w in store.values():
            if isinstance(w, ttk.Entry):
                w.delete(0, tk.END)
            elif isinstance(w, ttk.Combobox):
                w.current(0)

    # ══════════════════════════════════════════════════════════════
    # PESTAÑA PLANTAS
    # ══════════════════════════════════════════════════════════════
    def _tab_plantas(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="🏭 Plantas")

        ff = ttk.LabelFrame(frame, text="📝 Nueva Planta", padding=12)
        ff.pack(fill='x', padx=12, pady=8)
        self.ep = {}
        self._form(ff,
            [('Código *','codigo_planta'),('Nombre *','nombre_planta'),
             ('Ubicación','ubicacion_planta'),('Coordenadas (lat,lon)','coordenadas_planta'),
             ('Extensión (ha)','extension_planta')],
            [('Tipo','tipo_planta'),('Capacidad (MW)','capacidad_planta'),
             ('Inversión ($)','inversion_planta'),('Vida útil (años)','vida_util_planta'),
             ('Fecha marcha (AAAA-MM-DD)','fecha_marcha_planta')],
            self.ep,
            combos={'tipo_planta': ['solar_fotovoltaica','eolica','hidroelectrica','biomasa']})

        bf = ttk.Frame(ff)
        bf.grid(row=6, column=0, columnspan=4, pady=10)
        ttk.Button(bf, text="➕ Agregar",            command=self._agregar_planta).pack(side='left', padx=4)
        ttk.Button(bf, text="🗑️ Eliminar selec.",    command=self._eliminar_planta).pack(side='left', padx=4)
        ttk.Button(bf, text="🔄 Actualizar tabla",   command=self._cargar_plantas).pack(side='left', padx=4)

        tf = ttk.LabelFrame(frame, text="📋 Plantas Registradas", padding=8)
        tf.pack(fill='both', expand=True, padx=12, pady=8)
        self.tbl_plantas = self._tabla(tf,
            ('Código','Nombre','Tipo','Capacidad MW','Estado'),
            (110, 190, 150, 110, 110))
        self._cargar_plantas()

    # ══════════════════════════════════════════════════════════════
    # PESTAÑA EQUIPOS
    # ══════════════════════════════════════════════════════════════
    def _tab_equipos(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="⚙️ Equipos")

        ff = ttk.LabelFrame(frame, text="📝 Nuevo Equipo", padding=12)
        ff.pack(fill='x', padx=12, pady=8)
        self.ee = {}
        self._form(ff,
            [('N° Serie *','n_serie_equipo'),('Marca','marca_equipo'),
             ('Potencia (kW)','potencia_equipo')],
            [('Tipo específico','tipo_equipo'),('Modelo','modelo_equipo'),
             ('Eficiencia (%)','eficiencia_equipo')],
            self.ee)

        bf = ttk.Frame(ff)
        bf.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Button(bf, text="➕ Agregar",           command=self._agregar_equipo).pack(side='left', padx=4)
        ttk.Button(bf, text="🗑️ Eliminar selec.",   command=self._eliminar_equipo).pack(side='left', padx=4)
        ttk.Button(bf, text="🔄 Actualizar tabla",  command=self._cargar_equipos).pack(side='left', padx=4)

        tf = ttk.LabelFrame(frame, text="📋 Equipos Registrados", padding=8)
        tf.pack(fill='both', expand=True, padx=12, pady=8)
        self.tbl_equipos = self._tabla(tf,
            ('N° Serie','Tipo','Marca','Potencia MW','Estado'),
            (140, 150, 130, 110, 110))
        self._cargar_equipos()

    # ══════════════════════════════════════════════════════════════
    # PESTAÑA ESTACIONES
    # ══════════════════════════════════════════════════════════════
    def _tab_estaciones(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="🌤️ Estaciones")

        ff = ttk.LabelFrame(frame, text="📝 Nueva Estación Meteorológica", padding=12)
        ff.pack(fill='x', padx=12, pady=8)
        ff.columnconfigure(1, weight=1)
        self.est = {}
        for row, (lbl, key) in enumerate([
            ('Código *','codigo_estacion'), ('Ubicación','ubicacion_estacion'),
            ('Coordenadas (lat,lon)','coordenadas_estacion'),
            ('Equipos (separados por coma)','equipos_estacion'),
            ('Frecuencia','frecuencia_estacion'),
        ]):
            ttk.Label(ff, text=lbl).grid(row=row, column=0, sticky='w', pady=3, padx=(0,10))
            e = ttk.Entry(ff, width=40)
            e.grid(row=row, column=1, sticky='ew', pady=3)
            self.est[key] = e

        bf = ttk.Frame(ff)
        bf.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(bf, text="➕ Agregar",          command=self._agregar_estacion).pack(side='left', padx=4)
        ttk.Button(bf, text="🔄 Actualizar tabla", command=self._cargar_estaciones).pack(side='left', padx=4)

        tf = ttk.LabelFrame(frame, text="📋 Estaciones Registradas", padding=8)
        tf.pack(fill='both', expand=True, padx=12, pady=8)
        self.tbl_estaciones = self._tabla(tf,
            ('Código','Ubicación','Equipos','Estado'),
            (130, 220, 220, 110))
        self._cargar_estaciones()

    # ══════════════════════════════════════════════════════════════
    # PESTAÑA PRODUCCIÓN / DASHBOARD
    # ══════════════════════════════════════════════════════════════
    def _tab_produccion(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="📊 Dashboard")

        mf = ttk.LabelFrame(frame, text="📈 Métricas Generales (sp_dashboard_general)", padding=15)
        mf.pack(fill='x', padx=12, pady=8)

        self.lbl_m = {}
        items = [
            ('plantas_operativas',  '🏭 Plantas Operativas:',   '—'),
            ('produccion_hoy',      '⚡ Producción Hoy (MWh):', '—'),
            ('incidencias_abiertas','🚨 Incidencias Abiertas:',  '—'),
            ('energia_mes',         '📅 Energía Mes (MWh):',    '—'),
        ]
        for i, (key, lbl, val) in enumerate(items):
            col = (i % 2) * 2
            row = i // 2
            ttk.Label(mf, text=lbl, font=('Arial', 10, 'bold')).grid(
                row=row, column=col, sticky='w', pady=6, padx=(0,8))
            lv = ttk.Label(mf, text=val, font=('Arial', 11), foreground='#2980b9')
            lv.grid(row=row, column=col+1, sticky='w', pady=6, padx=(0,40))
            self.lbl_m[key] = lv

        ttk.Button(mf, text="🔄 Actualizar métricas",
                   command=self._cargar_metricas).grid(row=2, column=0, columnspan=4, pady=6)

        tf = ttk.LabelFrame(frame, text="⚡ Producción Reciente (vista_produccion_actual)", padding=8)
        tf.pack(fill='both', expand=True, padx=12, pady=8)
        self.tbl_prod = self._tabla(tf,
            ('Planta','Potencia MW','Energía MWh','Factor Cap.','Fecha / Hora'),
            (170, 110, 110, 100, 160))

        self._cargar_metricas()
        self._cargar_produccion()

    # ══════════════════════════════════════════════════════════════
    # PESTAÑA INCIDENCIAS
    # ══════════════════════════════════════════════════════════════
    def _tab_incidencias(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="🚨 Incidencias")

        ff = ttk.LabelFrame(frame, text="📝 Registrar Incidencia  (llama sp_crear_incidencia)", padding=12)
        ff.pack(fill='x', padx=12, pady=8)
        ff.columnconfigure(1, weight=1)
        self.inc = {}
        for row, (lbl, key) in enumerate([
            ('Código Planta *','codigo_planta'),
            ('Tipo incidencia *','tipo_incidencia'),
            ('Descripción *','descripcion'),
        ]):
            ttk.Label(ff, text=lbl).grid(row=row, column=0, sticky='w', pady=4, padx=(0,10))
            e = ttk.Entry(ff, width=45)
            e.grid(row=row, column=1, sticky='ew', pady=4)
            self.inc[key] = e

        bf = ttk.Frame(ff)
        bf.grid(row=4, column=0, columnspan=2, pady=8)
        ttk.Button(bf, text="📋 Registrar incidencia",  command=self._registrar_incidencia).pack(side='left', padx=4)
        ttk.Button(bf, text="🔄 Recargar lista",        command=self._cargar_incidencias).pack(side='left', padx=4)

        tf = ttk.LabelFrame(frame, text="📋 Incidencias Registradas", padding=8)
        tf.pack(fill='both', expand=True, padx=12, pady=8)
        self.tbl_inc = self._tabla(tf,
            ('Código','Planta','Tipo','Descripción','Impacto %','Estado','Fecha'),
            (110, 130, 120, 180, 80, 90, 145))
        self._cargar_incidencias()

    # ══════════════════════════════════════════════════════════════
    # PESTAÑA MANTENIMIENTOS
    # ══════════════════════════════════════════════════════════════
    def _tab_mantenimientos(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="🔧 Mantenimientos")

        ff = ttk.LabelFrame(frame, text="📝 Programar Mantenimiento  (llama sp_programar_mantenimiento)", padding=12)
        ff.pack(fill='x', padx=12, pady=8)
        ff.columnconfigure(1, weight=1)
        self.mant = {}

        ttk.Label(ff, text="Código Planta *").grid(row=0, column=0, sticky='w', pady=4, padx=(0,10))
        self.mant['codigo_planta'] = ttk.Entry(ff, width=22)
        self.mant['codigo_planta'].grid(row=0, column=1, sticky='ew', pady=4)

        ttk.Label(ff, text="Tipo *").grid(row=1, column=0, sticky='w', pady=4)
        self.mant['tipo'] = ttk.Combobox(ff, width=20, state='readonly',
                                          values=['preventivo','correctivo','predictivo'])
        self.mant['tipo'].set('preventivo')
        self.mant['tipo'].grid(row=1, column=1, sticky='ew', pady=4)

        ttk.Label(ff, text="Descripción *").grid(row=2, column=0, sticky='w', pady=4)
        self.mant['descripcion'] = ttk.Entry(ff, width=50)
        self.mant['descripcion'].grid(row=2, column=1, sticky='ew', pady=4)

        ttk.Label(ff, text="Técnicos (csv)").grid(row=3, column=0, sticky='w', pady=4)
        self.mant['tecnicos'] = ttk.Entry(ff, width=50)
        self.mant['tecnicos'].grid(row=3, column=1, sticky='ew', pady=4)

        bf = ttk.Frame(ff)
        bf.grid(row=4, column=0, columnspan=2, pady=8)
        ttk.Button(bf, text="📋 Programar mantenimiento", command=self._registrar_mantenimiento).pack(side='left', padx=4)
        ttk.Button(bf, text="🔄 Recargar lista",          command=self._cargar_mantenimientos).pack(side='left', padx=4)

        tf = ttk.LabelFrame(frame, text="📋 Mantenimientos Programados", padding=8)
        tf.pack(fill='both', expand=True, padx=12, pady=8)
        self.tbl_mant = self._tabla(tf,
            ('Orden','Planta','Tipo','Descripción','Fecha Prog.','Estado'),
            (120, 140, 100, 210, 115, 100))
        self._cargar_mantenimientos()

    # ══════════════════════════════════════════════════════════════
    # ACCIONES — Plantas
    # ══════════════════════════════════════════════════════════════
    def _agregar_planta(self):
        try:
            data = {k: (v.get() if hasattr(v,'get') else '') for k,v in self.ep.items()}
            if not data.get('codigo_planta','').strip():
                messagebox.showwarning("⚠️", "El Código es obligatorio."); return
            if agregar_planta(data):
                messagebox.showinfo("✅", f"Planta «{data['nombre_planta']}» guardada.")
                self._limpiar(self.ep); self._cargar_plantas(); self._cargar_metricas()
            else:
                messagebox.showerror("❌", "Código ya existe o datos inválidos.")
        except Exception as ex:
            messagebox.showerror("❌ Error", str(ex))

    def _eliminar_planta(self):
        sel = self.tbl_plantas.selection()
        if not sel: messagebox.showwarning("⚠️", "Selecciona una planta."); return
        cod = str(self.tbl_plantas.item(sel[0])['values'][0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar planta {cod}?"):
            try:
                eliminar_planta(cod); self._cargar_plantas(); self._cargar_metricas()
            except Exception as ex: messagebox.showerror("❌", str(ex))

    def _cargar_plantas(self):
        self.tbl_plantas.delete(*self.tbl_plantas.get_children())
        for p in obtener_plantas():
            self.tbl_plantas.insert('','end', values=(
                p.get('codigo_planta',''), p.get('nombre',''),
                p.get('tipo',''), p.get('capacidad_mw',''), p.get('estado_operativo','')))

    # ── Equipos ───────────────────────────────────────────────────
    def _agregar_equipo(self):
        try:
            data = {k: v.get() for k,v in self.ee.items()}
            if not data.get('n_serie_equipo','').strip():
                messagebox.showwarning("⚠️", "El N° Serie es obligatorio."); return
            if agregar_equipo(data):
                messagebox.showinfo("✅", "Equipo guardado.")
                self._limpiar(self.ee); self._cargar_equipos()
            else:
                messagebox.showerror("❌", "N° Serie ya existe o datos inválidos.")
        except Exception as ex:
            messagebox.showerror("❌", str(ex))

    def _eliminar_equipo(self):
        sel = self.tbl_equipos.selection()
        if not sel: messagebox.showwarning("⚠️", "Selecciona un equipo."); return
        serie = str(self.tbl_equipos.item(sel[0])['values'][0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar equipo {serie}?"):
            try:
                eliminar_equipo(serie); self._cargar_equipos()
            except Exception as ex: messagebox.showerror("❌", str(ex))

    def _cargar_equipos(self):
        self.tbl_equipos.delete(*self.tbl_equipos.get_children())
        for e in obtener_equipos():
            self.tbl_equipos.insert('','end', values=(
                e.get('numero_serie',''), e.get('tipo_especifico',''),
                e.get('marca',''), e.get('potencia_nominal_mw',''), e.get('estado_actual','')))

    # ── Estaciones ────────────────────────────────────────────────
    def _agregar_estacion(self):
        try:
            data = {k: v.get() for k,v in self.est.items()}
            if not data.get('codigo_estacion','').strip():
                messagebox.showwarning("⚠️", "El Código es obligatorio."); return
            if agregar_estacion(data):
                messagebox.showinfo("✅", "Estación guardada.")
                self._limpiar(self.est); self._cargar_estaciones()
            else:
                messagebox.showerror("❌", "Código ya existe.")
        except Exception as ex:
            messagebox.showerror("❌", str(ex))

    def _cargar_estaciones(self):
        self.tbl_estaciones.delete(*self.tbl_estaciones.get_children())
        for e in obtener_estaciones():
            eq = e.get('equipos_instalados','')
            if isinstance(eq, (list,dict)): eq = json.dumps(eq, ensure_ascii=False)
            self.tbl_estaciones.insert('','end', values=(
                e.get('codigo_estacion',''), e.get('ubicacion',''),
                eq, e.get('estado_funcionamiento','')))

    # ── Dashboard ─────────────────────────────────────────────────
    def _cargar_metricas(self):
        m = obtener_metricas()
        self.lbl_m['plantas_operativas'].config(text=str(m['plantas_operativas']))
        self.lbl_m['produccion_hoy'].config(text=f"{float(m['produccion_hoy']):.2f}")
        self.lbl_m['incidencias_abiertas'].config(text=str(m['incidencias_abiertas']))
        self.lbl_m['energia_mes'].config(text=f"{float(m['energia_mes']):.2f}")
        self._cargar_produccion()

    def _cargar_produccion(self):
        self.tbl_prod.delete(*self.tbl_prod.get_children())
        for r in obtener_produccion_reciente():
            self.tbl_prod.insert('','end', values=(
                r.get('planta',''), r.get('potencia_instantanea_mw',''),
                r.get('energia_generada_mwh',''), r.get('factor_capacidad',''),
                str(r.get('fecha_hora',''))))

    # ── Incidencias ───────────────────────────────────────────────
    def _registrar_incidencia(self):
        if not db.conectado:
            messagebox.showwarning("⚠️", "Requiere conexión a MySQL."); return
        cod_p = self.inc['codigo_planta'].get().strip()
        tipo  = self.inc['tipo_incidencia'].get().strip()
        desc  = self.inc['descripcion'].get().strip()
        if not all([cod_p, tipo, desc]):
            messagebox.showwarning("⚠️", "Todos los campos son obligatorios."); return
        try:
            c = db.conn.cursor()
            c.execute("CALL sp_crear_incidencia(%s,%s,%s,@cod)", (cod_p, tipo, desc))
            c.execute("SELECT @cod"); cod = c.fetchone()[0]; c.close()
            db.conn.commit()
            messagebox.showinfo("✅", f"Incidencia registrada: {cod}")
            self._limpiar(self.inc); self._cargar_incidencias(); self._cargar_metricas()
        except Exception as ex:
            messagebox.showerror("❌", str(ex))

    def _cargar_incidencias(self):
        self.tbl_inc.delete(*self.tbl_inc.get_children())
        for r in obtener_incidencias():
            self.tbl_inc.insert('','end', values=(
                r.get('codigo_incidencia',''), r.get('planta',''),
                r.get('tipo_incidencia',''), str(r.get('descripcion',''))[:50],
                r.get('impacto_produccion',''), r.get('estado',''),
                str(r.get('fecha_hora',''))))

    # ── Mantenimientos ────────────────────────────────────────────
    def _registrar_mantenimiento(self):
        if not db.conectado:
            messagebox.showwarning("⚠️", "Requiere conexión a MySQL."); return
        cod_p  = self.mant['codigo_planta'].get().strip()
        tipo   = self.mant['tipo'].get()
        desc   = self.mant['descripcion'].get().strip()
        tecs   = json.dumps([t.strip() for t in self.mant['tecnicos'].get().split(',') if t.strip()])
        if not all([cod_p, tipo, desc]):
            messagebox.showwarning("⚠️", "Código, tipo y descripción son obligatorios."); return
        try:
            c = db.conn.cursor()
            c.execute("CALL sp_programar_mantenimiento(%s,%s,%s,%s,@orden)", (cod_p, tipo, desc, tecs))
            c.execute("SELECT @orden"); orden = c.fetchone()[0]; c.close()
            db.conn.commit()
            messagebox.showinfo("✅", f"Mantenimiento programado: {orden}")
            self._limpiar(self.mant); self._cargar_mantenimientos()
        except Exception as ex:
            messagebox.showerror("❌", str(ex))

    def _cargar_mantenimientos(self):
        self.tbl_mant.delete(*self.tbl_mant.get_children())
        for r in obtener_mantenimientos():
            self.tbl_mant.insert('','end', values=(
                r.get('orden_trabajo',''), r.get('planta',''),
                r.get('tipo_mantenimiento',''), str(r.get('descripcion_actividades',''))[:50],
                str(r.get('fecha_programada','')), r.get('estado','')))

    # ── Menú utilidades ───────────────────────────────────────────
    def _reconectar(self):
        db.desconectar()
        if db.conectar():
            self.barra.config(
                text=f"✅ Reconectado  ·  {DB_CONFIG['database']}", bg="#27ae60")
            self._recargar_todo()
        else:
            self.barra.config(text="⚠️ Sin conexión — modo offline", bg="#e67e22")

    def _config_db(self):
        win = tk.Toplevel(self.root)
        win.title("⚙️ Configurar conexión MySQL")
        win.geometry("360x260")
        win.resizable(False, False)
        entries = {}
        for i, (lbl, key) in enumerate([
            ('Host','host'),('Puerto','port'),('Usuario','user'),
            ('Contraseña','password'),('Base de datos','database')
        ]):
            ttk.Label(win, text=lbl).grid(row=i, column=0, sticky='w', padx=15, pady=5)
            e = ttk.Entry(win, width=25, show='*' if key=='password' else '')
            e.insert(0, str(DB_CONFIG.get(key,'')))
            e.grid(row=i, column=1, padx=10, pady=5)
            entries[key] = e

        def guardar():
            for key, e in entries.items():
                val = e.get()
                DB_CONFIG[key] = int(val) if key == 'port' else val
            win.destroy()
            self._reconectar()

        ttk.Button(win, text="💾 Guardar y reconectar", command=guardar).grid(
            row=5, column=0, columnspan=2, pady=15)

    def _recargar_todo(self):
        self._cargar_plantas()
        self._cargar_equipos()
        self._cargar_estaciones()
        self._cargar_metricas()
        self._cargar_incidencias()
        self._cargar_mantenimientos()


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = GreenPowerApp(root)
    root.mainloop()