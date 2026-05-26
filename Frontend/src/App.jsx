import React, { useState } from 'react';
import { enviarPago } from './api';
import './App.css';

function App() {
  // 1. Nuevos estados para almacenar lo que el usuario digita
  const [cuentaOrigen, setCuentaOrigen] = useState('');
  const [cuentaDestino, setCuentaDestino] = useState('TDEA-MATRICULAS');
  const [monto, setMonto] = useState('');

  // Estados de la interfaz (los que ya tenías)
  const [mensaje, setMensaje] = useState('');
  const [cargando, setCargando] = useState(false);
  const [tipoMensaje, setTipoMensaje] = useState('');

  // 2. Nueva función para manejar el envío del formulario
  const manejarEnvio = async (e) => {
    e.preventDefault(); // Evita que la página recargue al darle al botón

    // Validación básica de campos vacíos
    if (!cuentaOrigen || !monto) {
      setMensaje('Por favor, completa todos los campos requeridos.');
      setTipoMensaje('error');
      return;
    }

    setCargando(true);
    setMensaje('Procesando transacción en Azure...');
    setTipoMensaje('info');
    
    // 3. Armamos el JSON con los datos reales del formulario
    const txData = {
      id: `TX-${Date.now()}`,
      monto: parseFloat(monto), // Aseguramos que se envíe como número
      cuenta_origen: cuentaOrigen,
      cuenta_destino: cuentaDestino
    };

    try {
      const response = await enviarPago(txData);
      if (response.ok) {
        setMensaje('¡Transacción exitosa! El pago ha sido registrado.');
        setTipoMensaje('exito');
        
        // Limpiamos los campos después de un pago exitoso
        setCuentaOrigen('');
        setMonto('');
      } else {
        setMensaje('Error: El servidor de Azure rechazó la petición.');
        setTipoMensaje('error');
      }
    } catch (error) {
      setMensaje('Error de conexión. Verifica que el backend esté activo.');
      setTipoMensaje('error');
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="app-container">
      <div className="payment-card">
        <div className="card-header">
          <h2>Portal de Pagos TdeA</h2>
          <p className="subtitle">Módulo de Transacciones PayFlow</p>
        </div>
        
        {/* 4. Cambiamos la vista estática por un formulario */}
        <form onSubmit={manejarEnvio} className="transaction-form">
          
          <div className="form-group">
            <label>ID Estudiante (Cuenta Origen):</label>
            <input 
              type="text" 
              value={cuentaOrigen}
              onChange={(e) => setCuentaOrigen(e.target.value)}
              placeholder="Ej: ESTUDIANTE-001"
              required
            />
          </div>

          <div className="form-group">
            <label>Concepto de Pago (Cuenta Destino):</label>
            <select 
              value={cuentaDestino}
              onChange={(e) => setCuentaDestino(e.target.value)}
            >
              <option value="TDEA-MATRICULAS">Pago de Matrícula</option>
              <option value="TDEA-DERECHOS-GRADO">Derechos de Grado</option>
              <option value="TDEA-CERTIFICADOS">Certificados Académicos</option>
              <option value="TDEA-UNIFORMES">Compra de Uniformes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Monto a pagar (COP):</label>
            <input 
              type="number" 
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="Ej: 1500000"
              min="1000"
              required
            />
          </div>

          <button 
            type="submit" 
            className={`pay-button ${cargando ? 'loading' : ''}`} 
            disabled={cargando}
          >
            {cargando ? 'Procesando Pago...' : 'Confirmar Pago'}
          </button>
        </form>

        {mensaje && (
          <div className={`status-message ${tipoMensaje}`}>
            {mensaje}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;