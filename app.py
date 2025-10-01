import os
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import func, desc
import datetime

# --- Importaciones desde models.py ---
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

# CORRECCIÓN DE ERROR (Revisado): Aseguramos que la URL usa 'postgresql://' en lugar de 'postgres://'.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

# --- Vincula la base de datos con la aplicación ---
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
                'success': True, 
                'message': f'¡Bienvenido {user.usuario}!', 
                'username': user.usuario, 
                'rol': user.rol
            })
        else:
            return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401
    except Exception as e:
        logger.error(f"Error en /login: {e}")
        return jsonify({"message": "Error interno del servidor"}), 500

# --- RUTAS CRUD (CREATE, READ, UPDATE, DELETE) ---

# --- Usuarios ---
@app.route('/usuarios', methods=['GET', 'POST'])
@app.route('/users', methods=['GET', 'POST'])
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
@app.route('/users/<string:username>', methods=['PUT', 'DELETE'])
def handle_usuario(username):
    user = Usuario.query.filter_by(usuario=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

    if request.method == 'PUT':
        data = request.get_json()
        if 'contraseña' in data and data['contraseña']:
            user.contraseña = data['contraseña']
        if 'rol' in data and data['rol']:
            user.rol = data['rol']
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario actualizado.'})

    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario eliminado.'})

# --- Empleados ---
@app.route('/empleados', methods=['GET', 'POST'])
@app.route('/employees', methods=['GET', 'POST']) 
def handle_empleados():
    if request.method == 'GET':
        items = Empleado.query.all()
        return jsonify([model_to_dict(item) for item in items])
    
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('cedula'):
            return jsonify({'success': False, 'message': 'La cédula es obligatoria.'}), 400
        
        if Empleado.query.filter_by(cedula=data['cedula']).first():
            return jsonify({'success': False, 'message': f'El empleado con cédula {data["cedula"]} ya existe.'}), 409
        
        data_to_save = {k: v for k, v in data.items() if v is not None and v != ''}
        new_item = Empleado(**data_to_save)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Empleado agregado.'}), 201

@app.route('/empleados/<string:cedula>', methods=['PUT'])
@app.route('/employees/<string:cedula>', methods=['PUT'])
def handle_empleado(cedula):
    item = Empleado.query.filter_by(cedula=cedula).first()
    if not item:
        return jsonify({'success': False, 'message': 'Empleado no encontrado.'}), 404
    
    data = request.get_json()
    for key, value in data.items():
        if hasattr(item, key):
            setattr(item, key, value)
            
    db.session.commit()
    return jsonify({'success': True, 'message': 'Empleado actualizado.'})

@app.route('/empleados/bulk', methods=['DELETE'])
@app.route('/employees/bulk', methods=['DELETE'])
def delete_empleados_bulk():
    data = request.get_json()
    cedulas_to_delete = data.get('cedulas', [])
    if not cedulas_to_delete:
        return jsonify({'success': False, 'message': 'No se proporcionaron cédulas.'}), 400
    
    num_deleted = Empleado.query.filter(Empleado.cedula.in_(cedulas_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    
    if num_deleted > 0:
        return jsonify({'success': True, 'message': f'{num_deleted} empleado(s) eliminado(s).'})
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
    item = Cliente.query.get(cliente_id)
    if not item: return jsonify({'success': False, 'message': 'Cliente no encontrado.'}), 404
    
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
    item = Proveedor.query.get(proveedor_id)
    if not item: return jsonify({'success': False, 'message': 'Proveedor no encontrado.'}), 404
    
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
    item = Banco.query.get(banco_id)
    if not item: return jsonify({'success': False, 'message': 'Movimiento no encontrado.'}), 404
    
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
@app.route('/materials', methods=['GET', 'POST'])
def handle_materials():
    if request.method == 'GET':
        items = LlegadaMaterial.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        new_item = LlegadaMaterial(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Material registrado.'}), 201

@app.route('/materials/<int:material_id>', methods=['PUT', 'DELETE'])
def handle_material(material_id):
    item = LlegadaMaterial.query.get(material_id)
    if not item: return jsonify({'success': False, 'message': 'Material no encontrado.'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Material actualizado.'})

    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Material eliminado.'})


@app.route('/materials/bulk', methods=['DELETE'])
def delete_materials_bulk():
    data = request.get_json()
    ids_to_delete = data.get('ids', [])
    if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
    LlegadaMaterial.query.filter(LlegadaMaterial.id.in_(ids_to_delete)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Material(es) eliminado(s).'})

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
    item = LlegadaTela.query.get(fabric_id)
    if not item: return jsonify({'success': False, 'message': 'Tela no encontrada.'}), 404
    
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
    
# --- Historial Tela ---
@app.route('/inventory/fabrics-history', methods=['GET'])
def get_fabrics_history():
    items = HistorialTela.query.order_by(HistorialTela.timestamp.desc()).all()
    return jsonify([model_to_dict(item) for item in items])


@app.route('/products', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'GET':
        items = ProductoTerminado.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        try:
            # --- SOLUCIÓN DE EMERGENCIA PARA NotNullViolation en 'id' ---
            # Si el ID no es auto-incrementable en la DB, lo generamos manualmente.
            # 1. Obtener el ID máximo actual.
            max_id = db.session.query(func.max(ProductoTerminado.id)).scalar()
            # Aseguramos que new_id sea un entero.
            new_id = int(max_id or 0) + 1
            
            # 2. Forzar la asignación del nuevo ID.
            data['id'] = new_id

            # Limpiamos 'lote' si viene nulo, ya que los logs indican que la base de datos lo espera.
            if 'lote' in data and data['lote'] is None:
                del data['lote']
            
            # Limpiamos 'fecha' si viene nulo (ya que los logs de la consola JS indican que se envía como cadena "29072025")
            if 'fecha' in data and data['fecha'] is None:
                del data['fecha']
            
            # Convertir valores numéricos que vienen del formulario/excel como string a sus tipos correctos
            # Esto es vital para que SQLAlchemy no intente mezclar tipos.
            for key in ['medida_trazo', 'trazos', 'cantidad', 'valor_confeccion', 'ganancia_percent', 'valor_total', 'valor_venta']:
                if key in data and isinstance(data[key], str):
                    try:
                        # Intentar convertir a float, que cubre enteros también.
                        data[key] = float(data[key])
                    except ValueError:
                        # Si no es convertible, dejarlo como está (puede ser un problema en la DB después, pero evita el error de tipo Python aquí)
                        pass 

            materials_used = data.get('materials_used', [])
            if isinstance(materials_used, str): materials_used = json.loads(materials_used)
            
            fabrics_used = data.get('fabrics_used', [])
            if isinstance(fabrics_used, str): fabrics_used = json.loads(fabrics_used)

            for item_mat in materials_used:
                material = LlegadaMaterial.query.get(item_mat['id'])
                # Asegurarse de que los valores sean float antes de comparar o restar
                quantity_used = float(item_mat['quantity_used']) if item_mat.get('quantity_used') else 0
                
                if not material or material.quantity_value < quantity_used:
                    # Si falla, hacemos rollback de la sesión ANTES de retornar el error.
                    db.session.rollback()
                    return jsonify({'success': False, 'message': f"Stock insuficiente para material ID {str(item_mat['id'])}"}), 400
                material.quantity_value -= quantity_used
            
            # CORRECCIÓN 2: Se usa la variable de iteración correcta 'item_fab' en lugar de 'fab_item'.
            for item_fab in fabrics_used:
                tela = LlegadaTela.query.get(item_fab['id'])
                # Asegurarse de que los valores sean float antes de comparar o restar
                quantity_used_fab = float(item_fab['quantity_used']) if item_fab.get('quantity_used') else 0

                if not tela or tela.cantidad_value < quantity_used_fab:
                    # Si falla, hacemos rollback de la sesión ANTES de retornar el error.
                    db.session.rollback()
                    return jsonify({'success': False, 'message': f"Stock insuficiente para tela ID {str(item_fab['id'])}"}), 400
                tela.cantidad_value -= quantity_used_fab
            
            # Serializar listas de uso a JSON string antes de guardar
            data['materials_used'] = json.dumps(materials_used)
            data['fabrics_used'] = json.dumps(fabrics_used)

            # Crear y registrar el nuevo producto (ahora 'data' contiene 'id').
            new_item = ProductoTerminado(**data)
            db.session.add(new_item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Producto registrado y stock actualizado.'}), 201

        except Exception as e:
            # Rollback en caso de cualquier otro error crítico (ej. error de conexión o tipo de dato)
            db.session.rollback()
            # Esto captura y registra el error de la BD. Convertimos la excepción a str para el logger.
            logger.error(f"Error registrando producto: {e}")
            return jsonify({'success': False, 'message': 'Error interno al registrar producto.'}), 500


@app.route('/products/last', methods=['GET'])
def get_last_product():
    try:
        last_product = db.session.query(ProductoTerminado).order_by(desc(ProductoTerminado.id)).first()
        if last_product:
            return jsonify(model_to_dict(last_product))
        else:
            return jsonify({'serial': '7300'})
    except Exception as e:
        logger.error(f"Error en /products/last: {e}")
        return jsonify({"message": "Error interno"}), 500

@app.route('/products/bulk', methods=['DELETE'])
def delete_products_bulk():
    ids = request.get_json().get('ids', [])
    if not ids: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
    try:
        products = ProductoTerminado.query.filter(ProductoTerminado.id.in_(ids)).all()
        for p in products:
            try:
                for mat in json.loads(p.materials_used or '[]'):
                    m = LlegadaMaterial.query.get(mat['id'])
                    if m: m.quantity_value += float(mat['quantity_used'])
                for fab in json.loads(p.fabrics_used or '[]'):
                    f = LlegadaTela.query.get(fab['id'])
                    if f: f.cantidad_value += float(fab['quantity_used'])
            except Exception as e:
                logger.warning(f"No se pudo reponer stock para producto ID {p.id}: {e}")
            db.session.delete(p)
        db.session.commit()
        return jsonify({'success': True, 'message': f'{len(products)} producto(s) eliminado(s).'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al eliminar productos.'}), 500
        

@app.route('/products/<string:product_id>', methods=['PUT', 'DELETE'])
def handle_product(product_id):
    item = ProductoTerminado.query.get(product_id)
    if not item: return jsonify({'success': False, 'message': 'Producto no encontrado.'}), 404

    if request.method == 'PUT':
        data = request.get_json()
        if 'materials_used' in data and isinstance(data['materials_used'], list):
            data['materials_used'] = json.dumps(data['materials_used'])
        if 'fabrics_used' in data and isinstance(data['fabrics_used'], list):
            data['fabrics_used'] = json.dumps(data['fabrics_used'])
            
        for key, value in data.items():
            if hasattr(item, key) and key != 'id': setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Producto actualizado.'})

    if request.method == 'DELETE':
        try:
            materials_to_return = json.loads(item.materials_used) if isinstance(item.materials_used, str) and item.materials_used else []
            fabrics_to_return = json.loads(item.fabrics_used) if isinstance(item.fabrics_used, str) and item.fabrics_used else []

            for mat_item in materials_to_return:
                material = LlegadaMaterial.query.get(mat_item['id'])
                if material: material.quantity_value += float(mat_item['quantity_used'])
            
            for fab_item in fabrics_to_return:
                tela = LlegadaTela.query.get(fab_item['id'])
                if tela: tela.cantidad_value += float(fab_item['quantity_used'])

            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Producto eliminado y stock repuesto.'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error eliminando producto: {e}")
            return jsonify({'success': False, 'message': 'Error al eliminar y reponer stock.'}), 500

# --- PagosSatelites ---
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
        data = request.get_json()
        try:
            products_sold = data.get('products_sold', [])
            if isinstance(products_sold, str): products_sold = json.loads(products_sold)

            for p_sold in products_sold:
                producto = ProductoTerminado.query.get(p_sold['id'])
                if not producto or producto.cantidad < float(p_sold['quantity']):
                    return jsonify({'success': False, 'message': f"Stock insuficiente para producto ID {p_sold['id']}"}), 400
                producto.cantidad -= float(p_sold['quantity'])
            
            data['products_sold'] = json.dumps(products_sold)
            new_item = Venta(**data)
            db.session.add(new_item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Venta registrada y stock actualizado.'}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error en venta: {e}")
            return jsonify({'success': False, 'message': 'Error al registrar venta.'}), 500

# --- Cortes ---
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
        
    if request.method == 'PUT':
        data = request.get_json()
        updates = data.get('updates', [])
        if not updates:
            return jsonify({'success': False, 'message': 'No se proporcionaron actualizaciones.'}), 400
        for update in updates:
            item = ProgramacionCorte.query.get(update.get('id'))
            if item:
                item.status = update.get('status')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estados actualizados.'})

    if request.method == 'DELETE':
        data = request.get_json()
        ids_to_delete = data.get('ids', [])
        if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
        ProgramacionCorte.query.filter(ProgramacionCorte.id.in_(ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Corte(s) eliminado(s).'})

# --- Asignaciones Satelite ---
@app.route('/assignments', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_assignments():
    if request.method == 'GET':
        items = AsignacionSatelite.query.all()
        return jsonify([model_to_dict(item) for item in items])
    if request.method == 'POST':
        data = request.get_json()
        if not data.get('total_price'):
            quantity = float(data.get('assigned_quantity', 0))
            price = float(data.get('unit_price', 0))
            data['total_price'] = quantity * price
        new_item = AsignacionSatelite(**data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201

    if request.method == 'PUT':
        data = request.get_json()
        item_id = data.get('id')
        item = AsignacionSatelite.query.get(item_id)
        if not item: return jsonify({'success': False, 'message': 'Asignación no encontrada.'}), 404
        for key, value in data.items():
            if hasattr(item, key): setattr(item, key, value)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Asignación actualizada.'})
        
    if request.method == 'DELETE':
        data = request.get_json()
        ids_to_delete = data.get('ids', [])
        if not ids_to_delete: return jsonify({'success': False, 'message': 'No se proporcionaron IDs.'}), 400
        AsignacionSatelite.query.filter(AsignacionSatelite.id.in_(ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Asignación(es) eliminada(s).'})

# --- Entregas Satelite ---
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
        
# --- Rutas de Inventario ---
@app.route('/inventory/summary', methods=['GET'])
def get_inventory_summary():
    summary = db.session.query(
        LlegadaMaterial.material_name,
        LlegadaMaterial.size_value,
        LlegadaMaterial.size_unit,
        LlegadaMaterial.quantity_type,
        func.sum(LlegadaMaterial.quantity_value).label('total_quantity')
    ).group_by(
        LlegadaMaterial.material_name,
        LlegadaMaterial.size_value,
        LlegadaMaterial.size_unit,
        LlegadaMaterial.quantity_type
    ).all()
    return jsonify([{
        'material_name': r.material_name, 'size_value': r.size_value, 'size_unit': r.size_unit,
        'quantity_type': r.quantity_type, 'total_quantity': float(r.total_quantity or 0)
    } for r in summary])

@app.route('/inventory/history', methods=['GET'])
def get_inventory_history():
    items = LlegadaMaterial.query.with_entities(
        LlegadaMaterial.entry_date.label('date'),
        LlegadaMaterial.material_name,
        LlegadaMaterial.quantity_value,
        LlegadaMaterial.quantity_type,
        LlegadaMaterial.supplier
    ).all()
    results = [dict(row._mapping) for row in items]
    for r in results:
        r['type'] = 'Ingreso'
        if isinstance(r['date'], (datetime.datetime, datetime.date)):
            r['date'] = r['date'].isoformat()
    return jsonify(results)

@app.route('/inventory/fabrics', methods=['GET'])
def get_inventory_fabrics():
    items = LlegadaTela.query.all()
    return jsonify([model_to_dict(item) for item in items])

# --- Dynamic Codes (Referencias y Códigos de Barras) ---
@app.route('/dynamic-codes/<string:type>/<string:category>', methods=['GET', 'POST', 'DELETE'])
def handle_dynamic_codes(type, category):
    if request.method == 'GET':
        items = DynamicCode.query.filter_by(type=type, category=category).all()
        return jsonify([model_to_dict(item) for item in items])
        
    if request.method == 'POST':
        data = request.get_json()
        code_data = {
            'type': type, 'category': category,
            'code': data.get('code'), 'description': data.get('description'),
            'costo_venta': data.get('costo_venta'), 'costo_confeccion': data.get('costo_confeccion')
        }
        new_item = DynamicCode(**code_data)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Código agregado.'}), 201

    if request.method == 'DELETE':
        data = request.get_json()
        ids_to_delete = data.get('ids', [])
        if not ids_to_delete:
            return jsonify({'success': False, 'message': 'No se proporcionaron IDs para eliminar.'}), 400
        
        num_deleted = DynamicCode.query.filter(
            DynamicCode.type == type,
            DynamicCode.category == category,
            DynamicCode.id.in_(ids_to_delete)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        if num_deleted > 0:
            return jsonify({'success': True, 'message': f'{num_deleted} registro(s) eliminado(s).'})
        return jsonify({'success': False, 'message': 'No se encontraron registros para eliminar.'}), 404

@app.route('/dynamic-codes/<string:type>/<string:category>/<int:item_id>', methods=['PUT'])
def handle_dynamic_code_item(type, category, item_id):
    item = DynamicCode.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Registro no encontrado.'}), 404
    
    if item.type != type or item.category != category:
        return jsonify({'success': False, 'message': 'La categoría del item no coincide.'}), 400
        
    data = request.get_json()
    item.code = data.get('code', item.code)
    item.description = data.get('description', item.description)
    item.costo_venta = data.get('costo_venta', item.costo_venta)
    item.costo_confeccion = data.get('costo_confeccion', item.costo_confeccion)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Registro actualizado.'})

# --- CORRECCIÓN CLAVE ---
@app.route('/dynamic-codes/all-references', methods=['GET'])
def get_all_references():
    items = DynamicCode.query.filter_by(type='reference').all()
    return jsonify([model_to_dict(item) for item in items])

# --- CORRECCIÓN CLAVE ---
@app.route('/dynamic-codes/all-barcodes', methods=['GET'])
def get_all_barcodes():
    return jsonify([])

# --- RUTAS DE LÓGICA DE NEGOCIO Y DASHBOARD ---

# --- KPIs ---
@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    try:
        kpis = {}
        deuda_c = db.session.query(func.sum(Cliente.valor - Cliente.abono)).scalar()
        kpis['deuda_clientes'] = float(deuda_c or 0)

        deuda_p = db.session.query(func.sum(Proveedor.valor - Proveedor.abono)).scalar()
        kpis['deuda_proveedores'] = float(deuda_p or 0)

        total_v = db.session.query(func.sum(Venta.total_sale)).scalar()
        kpis['total_ventas'] = float(total_v or 0)

        val_telas = db.session.query(func.sum(LlegadaTela.cantidad_value * LlegadaTela.unit_value)).scalar()
        kpis['valor_inventario_telas'] = float(val_telas or 0)

        val_mats = db.session.query(func.sum(LlegadaMaterial.quantity_value * LlegadaMaterial.unit_value)).scalar()
        kpis['valor_inventario_materiales'] = float(val_mats or 0)

        val_prod = db.session.query(func.sum(AsignacionSatelite.total_price)).filter(AsignacionSatelite.status == 'Asignado').scalar()
        kpis['valor_en_produccion'] = float(val_prod or 0)
        
        kpis['total_empleados'] = Empleado.query.count()

        return jsonify(kpis)
    except Exception as e:
        logger.error(f"Error en /api/kpis: {e}")
        return jsonify({"error": f"Error al calcular KPIs: {e}"}), 500

# --- Gráficos del Dashboard ---
@app.route('/api/charts/sales-trend', methods=['GET'])
def get_chart_sales_trend():
    try:
        results = db.session.query(
            func.to_char(Venta.sale_date, 'YYYY-MM'), 
            func.sum(Venta.total_sale)
        ).group_by(func.to_char(Venta.sale_date, 'YYYY-MM')).order_by(func.to_char(Venta.sale_date, 'YYYY-MM')).all()
        
        return jsonify({
            'labels': [r[0] for r in results],
            'data': [float(r[1] or 0) for r in results]
        })
    except Exception as e:
        logger.error(f"Error en chart/sales-trend: {e}")
        return jsonify({"error": "Error al procesar tendencia de ventas"}), 500

@app.route('/api/charts/cuts-status', methods=['GET'])
def get_chart_cuts_status():
    try:
        results = db.session.query(ProgramacionCorte.status, func.count(ProgramacionCorte.id)).group_by(ProgramacionCorte.status).all()
        return jsonify({
            'labels': [r[0] for r in results],
            'data': [r[1] for r in results]
        })
    except Exception as e:
        logger.error(f"Error en chart/cuts-status: {e}")
        return jsonify({"error": "Error al procesar estado de cortes"}), 500

@app.route('/api/charts/production-by-satellite', methods=['GET'])
def get_chart_production_by_satellite():
    try:
        results = db.session.query(
            AsignacionSatelite.satellite_name, 
            func.sum(AsignacionSatelite.total_price)
        ).group_by(AsignacionSatelite.satellite_name).order_by(func.sum(AsignacionSatelite.total_price).desc()).all()
        return jsonify({
            'labels': [r[0] for r in results],
            'data': [float(r[1] or 0) for r in results]
        })
    except Exception as e:
        logger.error(f"Error en chart/production-by-satellite: {e}")
        return jsonify({"error": "Error al procesar producción por satélite"}), 500
        
@app.route('/api/charts/fabrics-by-value', methods=['GET'])
def get_chart_fabrics_by_value():
    try:
        top_fabrics = db.session.query(
            LlegadaTela.tipo_de_tela,
            func.sum(LlegadaTela.cantidad_value * LlegadaTela.unit_value).label('total_value')
        ).group_by(LlegadaTela.tipo_de_tela).order_by(func.sum(LlegadaTela.cantidad_value * LlegadaTela.unit_value).desc()).limit(5).all()
        
        return jsonify({
            'labels': [r.tipo_de_tela for r in top_fabrics],
            'data': [float(r.total_value or 0) for r in top_fabrics]
        })
    except Exception as e:
        logger.error(f"Error en chart/fabrics-by-value: {e}")
        return jsonify({"error": "Error al procesar valor de telas"}), 500

@app.route('/api/charts/inventory-by-supplier', methods=['GET'])
def get_chart_inventory_by_supplier():
    try:
        fabrics_value = db.session.query(
            LlegadaTela.proveedor,
            func.sum(LlegadaTela.cantidad_value * LlegadaTela.unit_value).label('total')
        ).group_by(LlegadaTela.proveedor).subquery()
        
        materials_value = db.session.query(
            LlegadaMaterial.supplier.label('proveedor'),
            func.sum(LlegadaMaterial.quantity_value * LlegadaMaterial.unit_value).label('total')
        ).group_by(LlegadaMaterial.supplier).subquery()
        
        from sqlalchemy import union_all
        all_inventory = union_all(fabrics_value.select(), materials_value.select()).alias('all_inventory')
        
        results = db.session.query(
            all_inventory.c.proveedor,
            func.sum(all_inventory.c.total).label('grand_total')
        ).group_by(all_inventory.c.proveedor).order_by(func.sum(all_inventory.c.total).desc()).limit(10).all()

        return jsonify({
            'labels': [r.proveedor for r in results],
            'data': [float(r.grand_total or 0) for r in results]
        })
    except Exception as e:
        logger.error(f"Error en chart/inventory-by-supplier: {e}")
        return jsonify({"error": "Error al procesar inventario por proveedor"}), 500

# --- Creación de las tablas ---
with app.app_context():
    logger.info("Verificando y creando tablas de la base de datos si es necesario...")
    db.create_all()
    logger.info("Tablas listas.")

# --- Ejecución Principal ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
