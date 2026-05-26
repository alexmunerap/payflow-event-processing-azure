import azure.functions as func
import logging
import json
import pyodbc
import os
from azure.servicebus import ServiceBusClient, ServiceBusMessage
# IMPORTANTE: Añadimos el cliente para inyectar datos al Event Hub desde la API
from azure.eventhub import EventHubProducerClient, EventData 

app = func.FunctionApp()

# ====================================================================
# 1. FUNCIÓN NUEVA: La puerta de entrada para tu React (API HTTP)
# ====================================================================
@app.route(route="pagar", auth_level=func.AuthLevel.ANONYMOUS)
def recibir_pago_http(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP Trigger: Petición de pago recibida desde el frontend.')
    
    try:
        # Extraemos el JSON que envía tu botón de React
        req_body = req.get_json()
        
        # Nos conectamos al Event Hub para inyectar la transacción de forma segura
        conn_str = os.environ["EventHubConnectionString"]
        producer = EventHubProducerClient.from_connection_string(
            conn_str=conn_str, 
            eventhub_name="transactions-hub"
        )
        
        # Enviamos el mensaje al flujo de procesamiento
        with producer:
            event_data_batch = producer.create_batch()
            event_data_batch.add(EventData(json.dumps(req_body)))
            producer.send_batch(event_data_batch)
            
        return func.HttpResponse(
            json.dumps({"mensaje": "Transacción recibida y encolada con éxito"}),
            status_code=202,
            mimetype="application/json"
        )
        
    except ValueError:
        return func.HttpResponse("JSON inválido", status_code=400)
    except Exception as e:
        logging.error(f"Error en HTTP Trigger: {str(e)}")
        return func.HttpResponse("Error interno del servidor", status_code=500)


# ====================================================================
# 2. TU FUNCIÓN ORIGINAL: El procesador en segundo plano (Event Hub)
# ====================================================================
@app.event_hub_message_trigger(arg_name="azeventhub", 
                               event_hub_name="transactions-hub",
                               connection="EventHubConnectionString")
def main(azeventhub: func.EventHubEvent):
    logging.info('PayFlow Trigger: Nuevo evento interceptado desde Event Hub.')
    
    try:
        body = azeventhub.get_body().decode('utf-8')
        tx = json.loads(body)
        
        # Mapeo de variables extrayendo del JSON 
        tx_id = tx.get("id")
        monto = float(tx.get("monto", 0))
        origen = tx.get("cuenta_origen")
        destino = tx.get("cuenta_destino")
        
        # Lógica del umbral de criticidad 
        if monto >= 5000000:
            logging.warning(f"Monto {monto} es CRÍTICO (>= 5M). Desviando al Service Bus...")
            enviar_a_service_bus(tx)
        else:
            logging.info(f"Monto {monto} es Estándar (< 5M). Procesando...")
            
        # Esto se ejecutará SIEMPRE, sin importar el monto
        guardar_en_sql(tx_id, monto, origen, destino)
            
    except Exception as e:
        logging.error(f"Error procesando la transacción: {str(e)}")

def enviar_a_service_bus(tx_data):
    conn_str = os.environ["ServiceBusConnectionString"]
    with ServiceBusClient.from_connection_string(conn_str) as client:
        with client.get_queue_sender(queue_name="high-value-transactions") as sender:
            message = ServiceBusMessage(json.dumps(tx_data))
            sender.send_messages(message)
    logging.info("Mensaje transaccional enviado a la cola crítica.")

def guardar_en_sql(tx_id, monto, origen, destino):
    conn_str = os.environ["SQL_ConnectionString"]
    
    query = """
    INSERT INTO dbo.Transactions 
    (transaction_id, merchant_id, user_id, amount, currency, transaction_date, status, type, origin_channel) 
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?);
    """
    
    merchant_id = "MERCH-001"   
    user_id = origen            
    currency = "COP"            
    status = "En revision"         
    tipo_tx = "standard"         
    channel = "web"              
    
    with pyodbc.connect(conn_str) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (tx_id, merchant_id, user_id, monto, currency, status, tipo_tx, channel))
            conn.commit()
    logging.info("Transacción asentada de forma segura en la base de datos.")