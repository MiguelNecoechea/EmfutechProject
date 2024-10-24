from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('EyesTracking/EyesTracking.html')

# Manejo de evento para recibir coordenadas de simulación
@socketio.on('gaze_data')
def handle_gaze_data(data):
    print(f"Coordenadas recibidas: {data}")  # Imprimir las coordenadas en la consola del servidor
    emit('gaze_data', data)  # Enviar de vuelta al cliente para actualizar la visualización

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
