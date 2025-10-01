import os
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import func
import datetime

# --- 1. Importaciones desde models.py ---
# Asegúrate de que tu archivo models.py contenga estas clases.
from models import (
    db, Usuario, Empleado, Cliente, Proveedor, Banco, LlegadaMaterial, 
    LlegadaTela, HistorialTela, ProductoTerminado, ProgramacionCorte, 
    AsignacionSatelite, EntregaSatelite, PagoSatelite, Venta, 
    ProveedorHistorial, DynamicCode
)

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Configuración de la Base de Datos ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada.")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

# --- 2. Vincula la base de datos con la aplicación ---
db.init_app(app)

# --- Función Auxiliar para convertir modelos a diccionarios ---
def model_to_dict(model_instance):
    """Convierte una instancia de modelo SQLAlchemy a un diccionario."""
    if model_instance is None:
        return None
    d = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, (datetime.datetime, datetime.date)):
            d[column.name] = value.isoformat()
        elif isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
            try:
                d[column.name] = json.loads(value)
            except json.JSONDecodeError:
                d[column.name] = value
        else:
            d[column.name] = value
    return d

# --- RUTAS DE LA APLICACIÓN ---

# Sirve el index.html y otros archivos estáticos
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)
    
# --- RUTA DE HEALTH CHECK ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

# --- RUTA DE LOGIN ---
@app.route('/login', methods=['POST'])
def handle_login():
    try:
        username_form = request.form.get('username', '').strip()
        password_form = request.form.get('password', '').strip()
        if not username_form or not password_form:
            return jsonify({'success': False, 'message': 'Usuario y contraseña son requeridos.'}), 400
        user = Usuario.query.filter_by(usuario=username_form).first()
        if user and user.contraseña == password_form:
            return jsonify({
                'success': True, 'message': f'¡Bienvenido {user.usuario}!', 
                'username': user.usuario, 'rol': user.rol
            })
        else:
            return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401
    except Exception as e:
        logger.error(f"Error en /login: {e}")
        return jsonify({"message": "Error interno del servidor"}), 500

# --- RUTAS CRUD (CREATE, READ, UPDATE, DELETE) ---

# --- Usuarios ---
@app.route('/usuarios', methods=['GET', 'POST'])
def handle_usuarios():
    if request.method == 'GET':
        items = Usuario.query.all()
        return jsonify([{'id': item.id, 'usuario': item.usuario, 'rol': item.rol} for item in items])
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('usuario') or not data.get('contraseña'):
            return jsonify({'success': False, 'message': 'Usuario y contraseña son obligatorios.'}), 400
        if Usuario.query.filter_by(usuario=data['usuario']).first():
            return jsonify({'success': False, 'message': f'El usuario "{data["usuario"]}" ya existe.'}), 409
        new_item = Usuario(usuario=data['usuario'], contraseña=data['contraseña'], rol=data.get('rol'))
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario agregado correctamente.'}), 201

@app.route('/usuarios/<string:username>', methods=['PUT', 'DELETE'])
def handle_usuario(username):
    user = Usuario.query.filter_by(usuario=username).first_or_404()
    if request.method == 'PUT':
        data = request.get_json()
        if 'contraseña' in data and data['contraseña']: user.contraseña = data['contraseña']
        if 'rol' in data and data['rol']: user.rol = data['rol']
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario actualizado.'})
    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario eliminado.'})

# --- Rutas para Materiales y Referencias (usando DynamicCode) ---
@app.route('/materials', methods=['GET', 'POST'])
def handle_dynamic_materials():
    if request.method == 'GET':
        items = DynamicCode.query.filter_by(type='material').all()
        return jsonify({'materials': [model_to_dict(item) for item in items]})
    if request.method == 'POST':
        data = request.get_json()
        new_item = DynamicCode(type='material', category='General', code=data.get('nombre'), description=data.get('descripcion'), costo_venta=data.get('precio'))
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'Material agregado', 'material': model_to_dict(new_item)}), 201

@app.route('/materials/<int:material_id>', methods=['PUT', 'DELETE'])
def handle_dynamic_material(material_id):
    item = DynamicCode.query.get_or_404(material_id)
    if item.type != 'material': return jsonify({'message': 'ID no corresponde a un material'}), 404
    if request.method == 'PUT':
        data = request.get_json()
        item.code = data.get('nombre', item.code)
        item.costo_venta = data.get('precio', item.costo_venta)
        db.session.commit()
        return jsonify({'message': 'Material actualizado'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Material eliminado'}), 204

@app.route('/references', methods=['GET', 'POST'])
def handle_dynamic_references():
    if request.method == 'GET':
        items = DynamicCode.query.filter_by(type='reference').all()
        return jsonify({'references': [model_to_dict(item) for item in items]})
    if request.method == 'POST':
        data = request.get_json()
        material_ids = data.get('material_ids', [])
        description_payload = {'text': data.get('descripcion'), 'materials': material_ids}
        new_item = DynamicCode(type='reference', category=data.get('categoria'), code=data.get('nombre'), description=json.dumps(description_payload), costo_venta=data.get('costo_total'))
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'Referencia creada'}), 201

@app.route('/references/<int:reference_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_dynamic_reference(reference_id):
    item = DynamicCode.query.get_or_404(reference_id)
    if item.type != 'reference': return jsonify({'message': 'ID no corresponde a una referencia'}), 404
    if request.method == 'GET':
        details = model_to_dict(item)
        try:
            desc_payload = json.loads(item.description or '{}')
            material_ids = desc_payload.get('materials', [])
            materials = DynamicCode.query.filter(DynamicCode.id.in_(material_ids)).all()
            details['materials'] = [{'id': m.id, 'nombre': m.code, 'precio': m.costo_venta} for m in materials]
            details['descripcion'] = desc_payload.get('text', '')
        except (json.JSONDecodeError, TypeError):
            details['materials'] = []
            details['descripcion'] = item.description
        return jsonify(details)
    if request.method == 'PUT':
        data = request.get_json()
        material_ids = data.get('material_ids', [])
        description_payload = {'text': data.get('descripcion'), 'materials': material_ids}
        item.category = data.get('categoria', item.category)
        item.code = data.get('nombre', item.code)
        item.description = json.dumps(description_payload)
        item.costo_venta = data.get('costo_total', item.costo_venta)
        db.session.commit()
        return jsonify({'message': 'Referencia actualizada'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Referencia eliminada'})

# --- LlegadaTelas ---
@app.route('/fabrics', methods=['GET', 'POST'])
def handle_fabrics():
    if request.method == 'GET':
        items = LlegadaTela.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = LlegadaTela(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tela registrada.'}), 201

@app.route('/fabrics/<int:fabric_id>', methods=['PUT', 'DELETE'])
def handle_fabric(fabric_id):
    item = LlegadaTela.query.get_or_404(fabric_id)
    if request.method == 'PUT':
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tela actualizada.'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tela eliminada.'})

@app.route('/fabrics/bulk', methods=['DELETE'])
def delete_fabrics_bulk():
    data = request.get_json()
    ids_to_delete = data.get('ids', [])
    if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
    LlegadaTela.query.filter(LlegadaTela.id.in_(ids_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Tela(s) eliminada(s).'})
    
# --- Dynamic Codes (Para datalists en el frontend) ---
@app.route('/dynamic-codes/<string:type>/<string:category>', methods=['GET'])
def handle_dynamic_codes(type, category):
    items = DynamicCode.query.filter_by(type=type, category=category).all()
    return jsonify([model_to_dict(item) for item in items])
    
# --- Empleados ---
@app.route('/empleados', methods=['GET', 'POST'])
def handle_empleados():
    if request.method == 'GET':
        items = Empleado.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        if Empleado.query.filter_by(cedula=data.get('cedula')).first():
            return jsonify({'success': False, 'message': 'Empleado ya existe.'}), 409
        new_item = Empleado(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Empleado agregado.'}), 201

@app.route('/empleados/<string:cedula>', methods=['PUT'])
def handle_empleado(cedula):
    item = Empleado.query.filter_by(cedula=cedula).first_or_404()
    data = request.get_json()
    for key, value in data.items():
        if hasattr(item, key): setattr(item, key, value)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Empleado actualizado.'})

@app.route('/empleados/bulk', methods=['DELETE'])
def delete_empleados_bulk():
    data = request.get_json()
    cedulas_to_delete = data.get('cedulas', [])
    if not cedulas_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron cédulas.'}), 400
    num_deleted = Empleado.query.filter(Empleado.cedula.in_(cedulas_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    if num_deleted > 0: return jsonify({'success': True, 'message': f'{num_deleted} empleado(s) eliminado(s).'})
    return jsonify({'success': False, 'message': 'No se encontraron empleados con esas cédulas.'}), 404

# --- Clientes ---
@app.route('/clientes', methods=['GET', 'POST'])
def handle_clientes():
    if request.method == 'GET':
        items = Cliente.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = Cliente(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cliente agregado.'}), 201

@app.route('/clientes/<int:cliente_id>', methods=['PUT', 'DELETE'])
def handle_cliente(cliente_id):
    item = Cliente.query.get_or_404(cliente_id)
    if request.method == 'PUT':
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cliente actualizado.'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cliente eliminado.'})

@app.route('/clientes/bulk', methods=['DELETE'])
def delete_clientes_bulk():
    data = request.get_json()
    ids_to_delete = data.get('ids', [])
    if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
    num_deleted = Cliente.query.filter(Cliente.id.in_(ids_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    if num_deleted > 0: return jsonify({'success': True, 'message': f'{num_deleted} cliente(s) eliminado(s).'})
    return jsonify({'success': False, 'message': 'No se encontraron clientes.'}), 404
    
# --- Proveedores (y su historial) ---
@app.route('/proveedores', methods=['GET', 'POST'])
def handle_proveedores():
    if request.method == 'GET':
        items = Proveedor.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = Proveedor(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Proveedor agregado.'}), 201

@app.route('/proveedores/<int:proveedor_id>', methods=['PUT', 'DELETE'])
def handle_proveedor(proveedor_id):
    item = Proveedor.query.get_or_404(proveedor_id)
    if request.method == 'PUT':
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Proveedor actualizado.'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Proveedor eliminado.'})

@app.route('/proveedores/bulk', methods=['DELETE'])
def delete_proveedores_bulk():
    data = request.get_json()
    ids_to_delete = data.get('ids', [])
    if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
    num_deleted = Proveedor.query.filter(Proveedor.id.in_(ids_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    if num_deleted > 0: return jsonify({'success': True, 'message': f'{num_deleted} proveedor(es) eliminado(s).'})
    return jsonify({'success': False, 'message': 'No se encontraron proveedores.'}), 404

@app.route('/proveedores/history', methods=['GET', 'POST'])
def handle_providers_history():
    if request.method == 'GET':
        items = ProveedorHistorial.query.order_by(ProveedorHistorial.timestamp.desc()).all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        data['timestamp'] = datetime.datetime.utcnow()
        new_item = ProveedorHistorial(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Historial de proveedor guardado.'}), 201
        
# --- Bancos ---
@app.route('/bancos', methods=['GET', 'POST'])
def handle_bancos():
    if request.method == 'GET':
        items = Banco.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        data['fecha_registro'] = datetime.datetime.utcnow()
        new_item = Banco(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Movimiento bancario agregado.'}), 201

@app.route('/bancos/<int:banco_id>', methods=['PUT', 'DELETE'])
def handle_banco(banco_id):
    item = Banco.query.get_or_404(banco_id)
    if request.method == 'PUT':
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Movimiento actualizado.'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Movimiento eliminado.'})

@app.route('/bancos/bulk', methods=['DELETE'])
def delete_bancos_bulk():
    data = request.get_json()
    ids_to_delete = data.get('ids', [])
    if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
    num_deleted = Banco.query.filter(Banco.id.in_(ids_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    if num_deleted > 0: return jsonify({'success': True, 'message': f'{num_deleted} movimiento(s) eliminado(s).'})
    return jsonify({'success': False, 'message': 'No se encontraron movimientos.'}), 404

# --- LlegadaMaterial ---
@app.route('/material-arrivals', methods=['GET', 'POST'])
def handle_material_arrivals():
    if request.method == 'GET':
        items = LlegadaMaterial.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = LlegadaMaterial(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Llegada de material registrada.'}), 201

@app.route('/material-arrivals/<int:material_id>', methods=['PUT', 'DELETE'])
def handle_material_arrival(material_id):
    item = LlegadaMaterial.query.get_or_404(material_id)
    if request.method == 'PUT':
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Llegada de material actualizada.'})
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Llegada de material eliminada.'})

# --- ProductosTerminados ---
@app.route('/products', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'GET':
        items = ProductoTerminado.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        try:
            # Lógica para descontar stock
            # (Asumiendo que esta lógica es correcta según tu modelo de negocio)
            data['materials_used'] = json.dumps(data.get('materials_used', []))
            data['fabrics_used'] = json.dumps(data.get('fabrics_used', []))
            new_item = ProductoTerminado(**data)
            db.session.add(new_item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Producto registrado.'}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registrando producto: {e}")
            return jsonify({'success': False, 'message': 'Error interno al registrar producto.'}), 500

@app.route('/products/<string:product_id>', methods=['PUT', 'DELETE'])
def handle_product(product_id):
    item = ProductoTerminado.query.get_or_404(product_id)
    if request.method == 'PUT':
        # ... Lógica de actualización
        pass
    if request.method == 'DELETE':
        # ... Lógica de eliminación y reposición de stock
        pass

# --- Cortes, Asignaciones, Entregas y Pagos ---
@app.route('/cuts', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_cuts():
    if request.method == 'GET':
        items = ProgramacionCorte.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = ProgramacionCorte(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    if request.method == 'PUT': # Para actualizar status
        data = request.get_json()
        updates = data.get('updates', [])
        for update in updates:
            item = ProgramacionCorte.query.get(update.get('id'))
            if item: item.status = update.get('status')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estados actualizados.'})
    if request.method == 'DELETE':
        data = request.get_json()
        ids = data.get('ids', [])
        ProgramacionCorte.query.filter(ProgramacionCorte.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Corte(s) eliminado(s).'})

@app.route('/assignments', methods=['GET', 'POST'])
def handle_assignments():
    if request.method == 'GET':
        items = AsignacionSatelite.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = AsignacionSatelite(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201

@app.route('/deliveries', methods=['GET', 'POST'])
def handle_deliveries():
    if request.method == 'GET':
        items = EntregaSatelite.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = EntregaSatelite(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201

@app.route('/payments', methods=['GET', 'POST'])
def handle_payments():
    if request.method == 'GET':
        items = PagoSatelite.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = PagoSatelite(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Pago registrado.'}), 201

# --- Ventas ---
@app.route('/sales', methods=['GET', 'POST'])
def handle_sales():
    if request.method == 'GET':
        items = Venta.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        # ... Lógica de venta y descuento de stock de ProductoTerminado ...
        pass

# --- RUTAS DE LÓGICA DE NEGOCIO Y DASHBOARD ---
@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    try:
        kpis = {
            'deuda_clientes': float(db.session.query(func.sum(Cliente.valor - Cliente.abono)).scalar() or 0),
            'deuda_proveedores': float(db.session.query(func.sum(Proveedor.valor - Proveedor.abono)).scalar() or 0),
            'total_ventas': float(db.session.query(func.sum(Venta.total_sale)).scalar() or 0),
            'valor_inventario_telas': float(db.session.query(func.sum(LlegadaTela.cantidad_value * LlegadaTela.unit_value)).scalar() or 0),
            'valor_inventario_materiales': float(db.session.query(func.sum(LlegadaMaterial.quantity_value * LlegadaMaterial.unit_value)).scalar() or 0),
            'valor_en_produccion': float(db.session.query(func.sum(AsignacionSatelite.total_price)).filter(AsignacionSatelite.status == 'Asignado').scalar() or 0),
            'total_empleados': Empleado.query.count()
        }
        return jsonify(kpis)
    except Exception as e:
        logger.error(f"Error en /api/kpis: {e}")
        return jsonify({"error": f"Error al calcular KPIs: {e}"}), 500

@app.route('/api/charts/sales-trend', methods=['GET'])
def get_chart_sales_trend():
    try:
        results = db.session.query(func.to_char(Venta.sale_date, 'YYYY-MM'), func.sum(Venta.total_sale)).group_by(func.to_char(Venta.sale_date, 'YYYY-MM')).order_by(func.to_char(Venta.sale_date, 'YYYY-MM')).all()
        return jsonify({'labels': [r[0] for r in results], 'data': [float(r[1] or 0) for r in results]})
    except Exception as e: return jsonify({"error": "Error al procesar tendencia de ventas"}), 500

@app.route('/api/charts/cuts-status', methods=['GET'])
def get_chart_cuts_status():
    try:
        results = db.session.query(ProgramacionCorte.status, func.count(ProgramacionCorte.id)).group_by(ProgramacionCorte.status).all()
        return jsonify({'labels': [r[0] for r in results], 'data': [r[1] for r in results]})
    except Exception as e: return jsonify({"error": "Error al procesar estado de cortes"}), 500

@app.route('/api/charts/production-by-satellite', methods=['GET'])
def get_chart_production_by_satellite():
    try:
        results = db.session.query(AsignacionSatelite.satellite_name, func.sum(AsignacionSatelite.total_price)).group_by(AsignacionSatelite.satellite_name).order_by(func.sum(AsignacionSatelite.total_price).desc()).all()
        return jsonify({'labels': [r[0] for r in results], 'data': [float(r[1] or 0) for r in results]})
    except Exception as e: return jsonify({"error": "Error al procesar producción por satélite"}), 500

# --- Creación de las tablas ---
with app.app_context():
    logger.info("Verificando y creando tablas de la base de datos si es necesario...")
    db.create_all()
    logger.info("Tablas listas.")

# --- Ejecución Principal ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

