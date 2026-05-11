import pymongo
from datetime import datetime, timezone
import json

def start_mongo_audit(uri, db_name, collections_to_watch):
    """
    Inicia un Change Stream en segundo plano para escuchar eventos en las colecciones
    indicadas y guardar los logs en la colección AUDITORIA_LOGS.
    """
    try:
        client = pymongo.MongoClient(uri)
        db = client[db_name]
        
        # Asegurar que la colección de auditoría existe
        if "AUDITORIA_LOGS" not in db.list_collection_names():
            db.create_collection("AUDITORIA_LOGS")
            
        audit_collection = db["AUDITORIA_LOGS"]
        
        # Filtro para escuchar solo en las colecciones seleccionadas
        pipeline = [
            {"$match": {"ns.coll": {"$in": collections_to_watch}}}
        ]
        
        # full_document='updateLookup' asegura que en caso de update podamos tener
        # la versión completa del documento después del cambio (valores_new).
        with db.watch(pipeline, full_document='updateLookup') as stream:
            for change in stream:
                operacion = change.get("operationType")
                
                if operacion in ["insert", "update", "delete"]:
                    # Mapear a nuestra nomenclatura I, U, D
                    op_char = 'I'
                    if operacion == "update": 
                        op_char = 'U'
                    elif operacion == "delete": 
                        op_char = 'D'
                    
                    valores_old = None
                    valores_new = None
                    
                    if op_char == 'I':
                        valores_new = change.get("fullDocument", {})
                    elif op_char == 'U':
                        valores_new = change.get("fullDocument", {})
                        # El ID servirá de referencia base para valores_old
                        valores_old = {"_id": change.get("documentKey", {}).get("_id")}
                    elif op_char == 'D':
                        valores_old = {"_id": change.get("documentKey", {}).get("_id")}

                    # Extraer fecha del evento
                    cluster_time = change.get("clusterTime")
                    fecha_evento = cluster_time.as_datetime() if cluster_time else datetime.now(timezone.utc)
                    
                    log_doc = {
                        "fecha_hora": fecha_evento,
                        "usuario_bd": "mongodb_change_stream",
                        "tabla_nombre": change.get("ns", {}).get("coll", "unknown"),
                        "operacion": op_char,
                        "valores_new": json.dumps(valores_new, default=str) if valores_new else None,
                        "valores_old": json.dumps(valores_old, default=str) if valores_old else None,
                        "ip_cliente": "localhost"
                    }
                    
                    audit_collection.insert_one(log_doc)
                    
    except Exception as e:
        print(f"Error en Change Stream de MongoDB: {e}")
