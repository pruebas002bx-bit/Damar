# -*- coding: utf-8 -*-
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func

# --- 1. Configuración Básica de la Aplicación ---
app = Flask(__name__, static_folder='.', static_url_path='')

# Configura CORS para permitir peticiones desde tu frontend.
# Para producción, es mejor restringir los orígenes.
CORS(app, resources={r"/*": {"origins": "*"}})

# Configura un sistema de logging para ver información y errores.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. Configuración de la Base de Datos (PostgreSQL) ---
# La URL de conexión se tomará de una variable de entorno,
# lo cual es una práctica estándar para la seguridad en producción.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Si la variable no está, lanza un error para evitar arrancar sin BD.
    raise RuntimeError("Error: La variable de entorno DATABASE_URL no está configurada.")

# SQLAlchemy espera 'postgresql://' en lugar de 'postgres://' que algunas plataformas usan.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}

# Inicializa la extensión SQLAlchemy
db = SQLAlchemy(app)

# --- 3. Definición de los Modelos de Datos (Tablas) ---
# Cada clase representa una tabla en tu base de datos PostgreSQL.
# Esto reemplaza las hojas de tu archivo Excel.

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {'Usuario': self.usuario, 'Rol': self.rol}

class Empleado(db.Model):
    __tablename__ = 'empleados'
    id = db.Column(db.Integer, primary_key=True)
    codigo_empleado = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    rh = db.Column(db.String(10))
    sexo = db.Column(db.String(20))
    fecha_nacimiento = db.Column(db.Date)
    lugar_nacimiento = db.Column(db.String(100))
    role = db.Column(db.String(100))
    numero_contrato = db.Column(db.String(50))
    tipo_contrato = db.Column(db.String(50))
    fecha_inicio = db.Column(db.Date)
    fecha_fin_contrato = db.Column(db.Date)
    phone = db.Column(db.String(30))
    correo = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    eps = db.Column(db.String(100))
    arl = db.Column(db.String(100))
    caja = db.Column(db.String(100))
    pension = db.Column(db.String(100))
    emergencia1_nombre = db.Column(db.String(150))
    emergencia1_telefono = db.Column(db.String(30))
    emergencia1_parentesco = db.Column(db.String(50))
    emergencia2_nombre = db.Column(db.String(150))
    emergencia2_telefono = db.Column(db.String(30))
    emergencia2_parentesco = db.Column(db.String(50))

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    factura = db.Column(db.String(50), unique=True, nullable=False)
    referencia = db.Column(db.String(100))
    valor = db.Column(db.Float, default=0.0)
    abono = db.Column(db.Float, default=0.0)

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    proveedor = db.Column(db.String(150), nullable=False)
    factura = db.Column(db.String(50), nullable=False)
    tela = db.Column(db.String(100))
    valor = db.Column(db.Float, default=0.0)
    abono = db.Column(db.Float, default=0.0)
    vencimiento = db.Column(db.Date)
    pdf_path = db.Column(db.String(255))
    __table_args__ = (db.UniqueConstraint('proveedor', 'factura', name='uq_proveedor_factura'),)

class ProveedorHistorial(db.Model):
    __tablename__ = 'proveedores_historial'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    proveedor = db.Column(db.String(150))
    factura = db.Column(db.String(50))
    type = db.Column(db.String(50))
    details = db.Column(db.Text)

class Banco(db.Model):
    __tablename__ = 'bancos'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    banco = db.Column(db.String(100))
    punto_venta = db.Column(db.String(100))
    aprobacion = db.Column(db.String(100), unique=True)
    valor = db.Column(db.Float)
    cuenta = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

class LlegadaMaterial(db.Model):
    __tablename__ = 'llegada_material'
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date, nullable=False)
    barcode = db.Column(db.String(100))
    material_name = db.Column(db.String(150))
    size_value = db.Column(db.Float)
    size_unit = db.Column(db.String(20))
    quantity_value = db.Column(db.Float)
    quantity_type = db.Column(db.String(50))
    supplier = db.Column(db.String(150))
    invoice_value = db.Column(db.Float)
    unit_value = db.Column(db.Float)
    image_path = db.Column(db.String(255))

class LlegadaTela(db.Model):
    __tablename__ = 'llegada_telas'
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date, nullable=False)
    invoice_number = db.Column(db.String(50))
    serial_rollo = db.Column(db.String(100), unique=True, nullable=False)
    barcode = db.Column(db.String(100))
    tipo_de_tela = db.Column(db.String(100))
    referencia_de_tela = db.Column(db.String(100))
    proveedor = db.Column(db.String(150))
    invoice_value = db.Column(db.Float)
    unit_value = db.Column(db.Float)
    cantidad_value = db.Column(db.Float)
    cantidad_type = db.Column(db.String(50))
    size_value = db.Column(db.Float)
    size_unit = db.Column(db.String(20))
    color_image_path = db.Column(db.String(255))
    qr_image_path = db.Column(db.String(255))
    pdf_path = db.Column(db.String(255))

class HistorialTela(db.Model):
    __tablename__ = 'historial_telas'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fabric_id = db.Column(db.Integer, db.ForeignKey('llegada_telas.id'))
    serial_rollo = db.Column(db.String(100))
    type = db.Column(db.String(50))
    quantity_change = db.Column(db.Float)
    details = db.Column(db.Text)

class ProductoTerminado(db.Model):
    __tablename__ = 'productos_terminados'
    id = db.Column(db.String(36), primary_key=True) # Para UUID
    lote = db.Column(db.String(50))
    fecha = db.Column(db.Date)
    referencia = db.Column(db.String(150))
    codigo_barras = db.Column(db.String(100))
    medida_trazo = db.Column(db.Float)
    trazos = db.Column(db.Integer)
    cantidad = db.Column(db.Float)
    tipo_tela = db.Column(db.String(100))
    satellite = db.Column(db.String(150))
    serial = db.Column(db.String(50), unique=True)
    observacion = db.Column(db.Text)
    valor_confeccion = db.Column(db.Float)
    ganancia_percent = db.Column(db.Float)
    valor_total = db.Column(db.Float)
    valor_venta = db.Column(db.Float)
    materials_used = db.Column(db.JSON)
    fabrics_used = db.Column(db.JSON)
    has_sample = db.Column(db.Boolean, default=False)
    sample_code = db.Column(db.String(50))

class ProgramacionCorte(db.Model):
    __tablename__ = 'programacion_cortes'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    reference = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    colors = db.Column(db.String(200))
    size = db.Column(db.String(50))
    distribute_to = db.Column(db.String(150))
    status = db.Column(db.String(50), default='Programado')
    terminado = db.Column(db.Integer, default=0)
    restantes = db.Column(db.Integer, default=0)

class AsignacionSatelite(db.Model):
    __tablename__ = 'asignaciones_satelites'
    id = db.Column(db.Integer, primary_key=True)
    assignment_date = db.Column(db.Date, nullable=False)
    satellite_name = db.Column(db.String(150))
    product_lote = db.Column(db.String(100))
    assigned_quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='Asignado')
    has_sample = db.Column(db.Boolean, default=False)
    sample_code = db.Column(db.String(50))

class EntregaSatelite(db.Model):
    __tablename__ = 'entregas_satelites'
    id = db.Column(db.Integer, primary_key=True)
    delivery_date = db.Column(db.Date)
    product_serial = db.Column(db.String(100))
    product_lote = db.Column(db.String(100))
    delivered_quantity = db.Column(db.Float)
    satellite_name = db.Column(db.String(150))

class PagoSatelite(db.Model):
    __tablename__ = 'pagos_satelites'
    id = db.Column(db.Integer, primary_key=True)
    payment_date = db.Column(db.Date)
    satellite_name = db.Column(db.String(150))
    payment_amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    details = db.Column(db.Text)
    product_serial = db.Column(db.String(100))
    status = db.Column(db.String(50))
    partial_payment_value = db.Column(db.Float)
    observation = db.Column(db.Text)
    total_payment_amount = db.Column(db.Float)
    reference = db.Column(db.String(150))

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date)
    invoice_number = db.Column(db.String(50), unique=True)
    punto_venta = db.Column(db.String(100))
    products_sold = db.Column(db.JSON)
    efectivo = db.Column(db.Float)
    consignacion = db.Column(db.Float)
    banco_consignacion = db.Column(db.String(100))
    total_sale = db.Column(db.Float)

# Modelos para Referencias y Códigos de Barras (genéricos)
class DynamicCode(db.Model):
    __tablename__ = 'dynamic_codes'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False) # 'reference' o 'barcode'
    category = db.Column(db.String(50), nullable=False) # 'productos', 'telas', 'materiales'
    code = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    costo_venta = db.Column(db.Float)
    costo_confeccion = db.Column(db.Float)
    __table_args__ = (db.UniqueConstraint('type', 'category', 'code', name='uq_dynamic_code'),)

# --- 4. Rutas de la API (Endpoints) ---
# Se reescriben las rutas para usar SQLAlchemy en lugar de Pandas.

# Helper para convertir un objeto SQLAlchemy a un diccionario
def model_to_dict(model_instance):
    if model_instance is None:
        return None
    return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

# --- Login ---
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña requeridos.'}), 400

    user = Usuario.query.filter(func.lower(Usuario.usuario) == func.lower(username)).first()

    if user and user.contraseña == password:
        return jsonify({
            'success': True,
            'message': f'¡Bienvenido {user.usuario}!',
            'username': user.usuario,
            'rol': user.rol
        })
    else:
        return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401

# --- CRUD Genérico ---
def create_crud_routes(model, model_name):
    @app.route(f'/{model_name}', methods=['GET'])
    def get_all():
        items = model.query.all()
        return jsonify([model_to_dict(item) for item in items])

    @app.route(f'/{model_name}/<int:item_id>', methods=['GET'])
    def get_one(item_id):
        item = db.session.get(model, item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Registro no encontrado.'}), 404
        return jsonify(model_to_dict(item))
    
    @app.route(f'/{model_name}', methods=['POST'])
    def create():
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400
        
        # Elimina 'id' si viene en el payload para evitar conflictos
        data.pop('id', None)

        try:
            new_item = model(**data)
            db.session.add(new_item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Registro creado.', 'item': model_to_dict(new_item)}), 201
        except (IntegrityError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.error(f"Error al crear en {model_name}: {e}")
            # Extraer un mensaje de error más amigable si es posible
            error_info = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'unique constraint' in error_info.lower():
                 return jsonify({'success': False, 'message': 'Error: El valor ya existe y debe ser único.'}), 409
            return jsonify({'success': False, 'message': 'Error en la base de datos al crear.'}), 500

    @app.route(f'/{model_name}/<int:item_id>', methods=['PUT'])
    def update(item_id):
        item = db.session.get(model, item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Registro no encontrado.'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400

        try:
            for key, value in data.items():
                if hasattr(item, key) and key != 'id':
                    setattr(item, key, value)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Registro actualizado.', 'item': model_to_dict(item)})
        except (IntegrityError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.error(f"Error al actualizar en {model_name}: {e}")
            return jsonify({'success': False, 'message': 'Error en la base de datos al actualizar.'}), 500
            
    @app.route(f'/{model_name}', methods=['DELETE'])
    def delete_many():
        data = request.get_json()
        ids_to_delete = data.get('ids', [])
        if not ids_to_delete:
            return jsonify({'success': False, 'message': 'No se proporcionaron IDs para eliminar.'}), 400
        
        try:
            num_deleted = model.query.filter(model.id.in_(ids_to_delete)).delete(synchronize_session=False)
            db.session.commit()
            if num_deleted > 0:
                return jsonify({'success': True, 'message': f'{num_deleted} registro(s) eliminado(s).'})
            else:
                return jsonify({'success': False, 'message': 'No se encontraron registros con los IDs proporcionados.'}), 404
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error al eliminar en {model_name}: {e}")
            return jsonify({'success': False, 'message': 'Error en la base de datos al eliminar.'}), 500

# --- Crear las rutas CRUD para cada modelo ---
# La ruta será el nombre de la tabla (ej. /usuarios, /empleados)
create_crud_routes(Usuario, Usuario.__tablename__)
create_crud_routes(Empleado, Empleado.__tablename__)
create_crud_routes(Cliente, Cliente.__tablename__)
create_crud_routes(Proveedor, Proveedor.__tablename__)
create_crud_routes(Banco, Banco.__tablename__)
create_crud_routes(LlegadaMaterial, 'materials') # Ruta personalizada
create_crud_routes(LlegadaTela, 'fabrics') # Ruta personalizada
create_crud_routes(ProgramacionCorte, 'cuts') # Ruta personalizada
create_crud_routes(AsignacionSatelite, 'assignments') # Ruta personalizada
create_crud_routes(EntregaSatelite, 'deliveries') # Ruta personalizada
create_crud_routes(PagoSatelite, 'payments') # Ruta personalizada
create_crud_routes(Venta, 'sales') # Ruta personalizada
# Nota: Productos y otros con lógica más compleja tendrán rutas personalizadas.

# --- Rutas con lógica específica ---

@app.route('/dynamic-codes/<type>/<category>', methods=['GET', 'POST'])
def handle_dynamic_data(type, category):
    if request.method == 'GET':
        items = DynamicCode.query.filter_by(type=type, category=category).all()
        return jsonify([model_to_dict(item) for item in items])

    if request.method == 'POST':
        data = request.get_json()
        code_value = data.get('code', '').strip()
        if not code_value:
            return jsonify({'success': False, 'message': 'El valor no puede estar vacío.'}), 400

        exists = DynamicCode.query.filter_by(type=type, category=category, code=code_value).first()
        if exists:
            return jsonify({'success': False, 'message': f'El valor "{code_value}" ya existe.'}), 409

        new_code = DynamicCode(type=type, category=category, **data)
        db.session.add(new_code)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Registro agregado.'}), 201

# --- KPIs y Gráficos ---

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    try:
        kpis = {}
        # Usamos `func.coalesce` para manejar valores nulos y evitar errores.
        kpis['deuda_clientes'] = db.session.query(func.sum(func.coalesce(Cliente.valor, 0) - func.coalesce(Cliente.abono, 0))).scalar() or 0.0
        kpis['deuda_proveedores'] = db.session.query(func.sum(func.coalesce(Proveedor.valor, 0) - func.coalesce(Proveedor.abono, 0))).scalar() or 0.0
        kpis['total_ventas'] = db.session.query(func.sum(Venta.total_sale)).scalar() or 0.0
        kpis['valor_inventario_telas'] = db.session.query(func.sum(func.coalesce(LlegadaTela.cantidad_value, 0) * func.coalesce(LlegadaTela.unit_value, 0))).scalar() or 0.0
        kpis['valor_inventario_materiales'] = db.session.query(func.sum(func.coalesce(LlegadaMaterial.quantity_value, 0) * func.coalesce(LlegadaMaterial.unit_value, 0))).scalar() or 0.0
        
        today_str = datetime.utcnow().date()
        kpis['cortes_pendientes_hoy'] = ProgramacionCorte.query.filter(ProgramacionCorte.date == today_str, ProgramacionCorte.status == 'Programado').count()
        
        kpis['valor_en_produccion'] = db.session.query(func.sum(AsignacionSatelite.total_price)).filter(AsignacionSatelite.status == 'Asignado').scalar() or 0.0
        kpis['total_empleados'] = Empleado.query.count()

        return jsonify(kpis)
    except Exception as e:
        logger.error(f"Error crítico en /api/kpis: {e}")
        return jsonify({"error": f"Error al calcular KPIs: {e}"}), 500

@app.route('/api/charts/sales-trend', methods=['GET'])
def get_chart_sales_trend():
    try:
        # Agrupar ventas por mes
        sales_by_month = db.session.query(
            func.to_char(Venta.sale_date, 'YYYY-MM').label('month'),
            func.sum(Venta.total_sale).label('total')
        ).group_by('month').order_by('month').all()
        
        return jsonify({
            'labels': [row.month for row in sales_by_month],
            'data': [row.total for row in sales_by_month]
        })
    except Exception as e:
        logger.error(f"Error en chart/sales-trend: {e}")
        return jsonify({"error": "Error al procesar tendencia de ventas"}), 500
        
# --- 5. Punto de Entrada de la Aplicación ---
if __name__ == '__main__':
    # El comando `db.create_all()` crea las tablas en la base de datos
    # basándose en los modelos que definiste.
    # Es seguro ejecutarlo múltiples veces; no recreará tablas que ya existen.
    with app.app_context():
        logger.info("Verificando y creando tablas de la base de datos si es necesario...")
        db.create_all()
        logger.info("Tablas listas.")

    # Inicia el servidor Flask.
    # En producción (como en OnRender), un servidor WSGI como Gunicorn
    # se encargará de esto. `app.run` es para desarrollo local.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
