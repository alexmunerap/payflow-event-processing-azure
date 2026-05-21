import azure.functions as func
import logging
import json
import pyodbc
import os
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()

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
            logging.info(f"Monto {monto} es Estándar (< 5M). Guardando en Azure SQL...")
            # Pasamos exactamente las variables extraídas
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
    
    # Consulta ajustada a las columnas reales de tu tabla en Azure (9 columnas = 9 signos ?)
    query = """
    INSERT INTO dbo.Transactions 
    (transaction_id, merchant_id, user_id, amount, currency, transaction_date, status, type, origin_channel) 
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?);
    """
    
    # Mapeamos tus variables a la estructura de la base de datos
    merchant_id = "MERCH-001"   
    user_id = origen            
    currency = "COP"            
    status = "En revision"         
    tipo_tx = "standard"         
    channel = "web"              
    
    with pyodbc.connect(conn_str) as conn:
        with conn.cursor() as cursor:
            # Los 8 argumentos en tupla que llenarán los signos '?' de la query
            cursor.execute(query, (tx_id, merchant_id, user_id, monto, currency, status, tipo_tx, channel))
            conn.commit()
    logging.info("Transacción asentada de forma segura en la base de datos.")