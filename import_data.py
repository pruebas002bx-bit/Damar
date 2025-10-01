import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
from flask import Flask

# --- 1. Importa la base de datos y los modelos desde models.py ---
from models import db, Usuario, Empleado, Cliente, Proveedor, Banco, LlegadaMaterial, LlegadaTela, HistorialTela, ProductoTerminado, ProgramacionCorte, AsignacionSatelite, EntregaSatelite, PagoSatelite, Venta, ProveedorHistorial, DynamicCode

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 2. Configuración de la Conexión a la Base de Datos ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("Error: La variable de entorno DATABASE_URL no está configurada.")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# --- 3. Mapeo de Hojas de Excel a Nombres de Tablas ---
SHEET_TO_TABLE_MAP = {
    'Usuarios': 'usuarios',
    'Empleados': 'empleados',
    'Clientes': 'clientes',
    'Proveedores': 'proveedores',
    'Bancos': 'bancos',
    'LlegadaMaterial': 'llegada_material',
    'LlegadaTelas': 'llegada_telas',
    'HistorialTelas': 'historial_telas',
    'ProductosTerminados': 'productos_terminados',
    'ProgramacionCortes': 'programacion_cortes',
    'AsignacionesSatelites': 'asignaciones_satelites',
    'EntregasSatelites': 'entregas_satelites',
    'PagosSatelites': 'pagos_satelites',
    'Ventas': 'ventas',
    'ProveedoresHistorial': 'proveedores_historial'
}

# --- 4. Función Principal de Importación ---
def import_sheet_to_table(excel_path, sheet_name, table_name):
    try:
        logging.info(f"Procesando hoja '{sheet_name}' para la tabla '{table_name}'...")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        df.columns = df.columns.str.strip().str.lower()
        df.rename(columns={'banco _consignacion': 'banco_consignacion'}, inplace=True)
        
        # Reemplazar NaN por None para compatibilidad con la base de datos
        df = df.where(pd.notna(df), None)
        
        data = df.to_dict(orient='records')

        if not data:
            logging.warning(f"No hay datos para importar en la hoja '{sheet_name}'.")
            return

        logging.info(f"Insertando {len(data)} registros en la tabla '{table_name}'...")
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                # Limpiar la tabla antes de insertar
                truncate_command = text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')
                connection.execute(truncate_command)
                
                # Obtener la estructura de la tabla para insertar solo columnas válidas
                from sqlalchemy import Table, MetaData
                meta = MetaData()
                meta.reflect(bind=connection)
                table_obj = meta.tables[table_name]
                
                # Filtrar los datos para que solo contengan columnas que existen en la tabla
                valid_data = []
                for row in data:
                    valid_row = {k: v for k, v in row.items() if k in table_obj.c}
                    valid_data.append(valid_row)

                if valid_data:
                    # Inserción masiva
                    connection.execute(table_obj.insert(), valid_data)
                
                trans.commit()
                logging.info(f"¡Éxito! Datos de '{sheet_name}' importados a '{table_name}'.")
            except Exception as e:
                trans.rollback()
                logging.error(f"FALLÓ la importación para '{sheet_name}'. Error: {e}")
    except Exception as e:
        logging.error(f"FALLÓ la lectura de la hoja '{sheet_name}'. Error: {e}")

# --- 5. Ejecución del Script ---
if __name__ == "__main__":
    EXCEL_FILE_NAME = 'datos.xlsx' # El nombre de tu archivo Excel
    
    # --- Creación de Tablas ---
    # Se crea una aplicación Flask temporal solo para usar su contexto y crear las tablas.
    temp_app = Flask(__name__)
    temp_app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(temp_app)

    with temp_app.app_context():
        logging.info("Verificando y creando tablas de la base de datos si es necesario...")
        db.create_all()
        logging.info("Tablas listas.")
    # --- Fin de Creación de Tablas ---

    if not os.path.exists(EXCEL_FILE_NAME):
        logging.error(f"El archivo '{EXCEL_FILE_NAME}' no fue encontrado en esta carpeta.")
    else:
        logging.info("--- INICIANDO SCRIPT DE MIGRACIÓN DE DATOS DESDE EXCEL ---")
        for sheet, table in SHEET_TO_TABLE_MAP.items():
            try:
                import_sheet_to_table(EXCEL_FILE_NAME, sheet, table)
            except Exception as e:
                 logging.warning(f"No se pudo procesar la hoja '{sheet}'. Error: {e}")
        logging.info("--- SCRIPT DE MIGRACIÓN FINALIZADO ---")

