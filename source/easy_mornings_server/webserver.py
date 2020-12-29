from bottle import Bottle, run, request, abort
from .lightmanager import LightManager


class WebServer:

    def __init__(self, light_manager: LightManager):
        app = Bottle()

        @app.post('/on')
        def on():
            light_manager.on()
            return {'success': True}

        @app.post('/off')
        def off():
            light_manager.off()
            return {'success': True}

        @app.post('/on-timer')
        def on():
            period = int(request.query.seconds)
            light_manager.on_timed(period)
            return {'success': True}

        @app.post('/fade-on')
        def on():
            period = int(request.query.seconds)
            light_manager.fade_on(period)
            return {'success': True}

        @app.post('/fade-off')
        def on():
            period = int(request.query.seconds)
            light_manager.fade_off(period)
            return {'success': True}

        @app.get('/status')
        def get_status():
            state = light_manager.state.state
            return {'state': state}

        run(app, host='0.0.0.0', port=8080)
