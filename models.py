from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, JSON

# Inicializa la extensión de base de datos. 
# No está vinculada a ninguna aplicación Flask todavía.
db = SQLAlchemy()

# --- MODELOS DE BASE DE DATOS ---
# Cada clase es una tabla en la base de datos.

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50))

class Empleado(db.Model):
    __tablename__ = 'empleados'
    codigo_empleado = db.Column(db.String(50), primary_key=True)
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
    fecha_fin_contrato = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(20))
    correo = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    eps = db.Column(db.String(100))
    arl = db.Column(db.String(100))
    caja = db.Column(db.String(100))
    pension = db.Column(db.String(100))
    emergencia1_nombre = db.Column(db.String(150))
    emergencia1_telefono = db.Column(db.String(20))
    emergencia1_parentesco = db.Column(db.String(50))
    emergencia2_nombre = db.Column(db.String(150))
    emergencia2_telefono = db.Column(db.String(20))
    emergencia2_parentesco = db.Column(db.String(50))

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)
    factura = db.Column(db.String(100), unique=True)
    referencia = db.Column(db.String(150))
    valor = db.Column(db.Float)
    abono = db.Column(db.Float)

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)
    proveedor = db.Column(db.String(150))
    factura = db.Column(db.String(100))
    tela = db.Column(db.String(150))
    valor = db.Column(db.Float)
    abono = db.Column(db.Float)
    vencimiento = db.Column(db.Date)
    pdf_path = db.Column(db.String(255))

class Banco(db.Model):
    __tablename__ = 'bancos'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)
    banco = db.Column(db.String(100))
    punto_venta = db.Column(db.String(100))
    aprobacion = db.Column(db.String(100), unique=True)
    valor = db.Column(db.Float)
    cuenta = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    descripcion = db.Column(Text)
    fecha_registro = db.Column(db.DateTime)

class LlegadaMaterial(db.Model):
    __tablename__ = 'llegada_material'
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date)
    barcode = db.Column(db.String(150))
    material_name = db.Column(db.String(150))
    size_value = db.Column(db.String(50))
    size_unit = db.Column(db.String(50))
    quantity_value = db.Column(db.Float)
    quantity_type = db.Column(db.String(50))
    supplier = db.Column(db.String(150))
    invoice_value = db.Column(db.Float)
    unit_value = db.Column(db.Float)
    image_path = db.Column(db.String(255))

class LlegadaTela(db.Model):
    __tablename__ = 'llegada_telas'
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date)
    invoice_number = db.Column(db.String(100))
    serial_rollo = db.Column(db.String(100), unique=True)
    barcode = db.Column(db.String(150))
    tipo_de_tela = db.Column(db.String(150))
    referencia_de_tela = db.Column(db.String(150))
    proveedor = db.Column(db.String(150))
    invoice_value = db.Column(db.Float)
    unit_value = db.Column(db.Float)
    cantidad_value = db.Column(db.Float)
    cantidad_type = db.Column(db.String(50))
    size_value = db.Column(db.String(50))
    size_unit = db.Column(db.String(50))
    color_image_path = db.Column(db.String(255))
    qr_image_path = db.Column(db.String(255))
    pdf_path = db.Column(db.String(255))

class HistorialTela(db.Model):
    __tablename__ = 'historial_telas'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    fabric_id = db.Column(db.Integer)
    serial_rollo = db.Column(db.String(100))
    type = db.Column(db.String(50))
    quantity_change = db.Column(db.Float)
    details = db.Column(Text)

class ProductoTerminado(db.Model):
    __tablename__ = 'productos_terminados'
    id = db.Column(db.String(100), primary_key=True)
    lote = db.Column(db.String(100))
    fecha = db.Column(db.Date)
    referencia = db.Column(db.String(150))
    codigo_barras = db.Column(db.String(150))
    medida_trazo = db.Column(db.Float)
    trazos = db.Column(db.Integer)
    cantidad = db.Column(db.Float)
    tipo_tela = db.Column(db.String(150))
    satellite = db.Column(db.String(150))
    serial = db.Column(db.String(100), unique=True)
    observacion = db.Column(Text)
    valor_confeccion = db.Column(db.Float)
    ganancia_percent = db.Column(db.Float)
    valor_total = db.Column(db.Float)
    valor_venta = db.Column(db.Float)
    materials_used = db.Column(JSON)
    fabrics_used = db.Column(JSON)
    has_sample = db.Column(db.Boolean)
    sample_code = db.Column(db.String(100))

class ProgramacionCorte(db.Model):
    __tablename__ = 'programacion_cortes'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    reference = db.Column(db.String(150))
    quantity = db.Column(db.Float)
    colors = db.Column(db.String(255))
    size = db.Column(db.String(50))
    distribute_to = db.Column(db.String(150))
    status = db.Column(db.String(50))
    terminado = db.Column(db.Float)
    restantes = db.Column(db.Float)

class AsignacionSatelite(db.Model):
    __tablename__ = 'asignaciones_satelites'
    id = db.Column(db.Integer, primary_key=True)
    assignment_date = db.Column(db.Date)
    satellite_name = db.Column(db.String(150))
    product_lote = db.Column(db.String(100))
    assigned_quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(50))
    has_sample = db.Column(db.Boolean)
    sample_code = db.Column(db.String(100))

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
    details = db.Column(Text)
    product_serial = db.Column(db.String(100))
    status = db.Column(db.String(50))
    partial_payment_value = db.Column(db.Float)
    observation = db.Column(Text)
    total_payment_amount = db.Column(db.Float)
    reference = db.Column(db.String(150))

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date)
    invoice_number = db.Column(db.String(100), unique=True)
    punto_venta = db.Column(db.String(100))
    products_sold = db.Column(JSON)
    efectivo = db.Column(db.Float)
    consignacion = db.Column(db.Float)
    banco_consignacion = db.Column(db.String(100))
    total_sale = db.Column(db.Float)

class ProveedorHistorial(db.Model):
    __tablename__ = 'proveedores_historial'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    proveedor = db.Column(db.String(150))
    factura = db.Column(db.String(100))
    type = db.Column(db.String(50))
    details = db.Column(Text)

class DynamicCode(db.Model):
    __tablename__ = 'dynamic_codes'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50)) # 'reference' or 'barcode'
    category = db.Column(db.String(50)) # 'products', 'fabrics', 'materials'
    code = db.Column(db.String(255), nullable=False)
    description = db.Column(Text)
    costo_venta = db.Column(db.Float)
    costo_confeccion = db.Column(db.Float)
