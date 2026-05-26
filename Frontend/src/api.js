// Frontend/src/api.js
const API_URL = "https://func-payflow-processor-f0gvbgfrcadvf0a2.brazilsouth-01.azurewebsites.net/api/pagar";

export const enviarPago = async (datosTransaccion) => {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datosTransaccion)
  });
  return response;
};