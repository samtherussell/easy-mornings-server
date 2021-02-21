from bottle import Bottle, run, request
from .lightmanager import LightManager


class WebServer:

    def __init__(self, light_manager: LightManager):
        app = Bottle()

        @app.post('/on')
        def on():
            level = request.query.level
            level = float(level) if level else None
            light_manager.on(level)
            return {'success': True}

        @app.post('/off')
        def off():
            light_manager.off()
            return {'success': True}

        @app.post('/on-timer')
        def on_timer():
            period = int(request.query.seconds)
            light_manager.on_timed(period)
            return {'success': True}

        @app.post('/fade-on')
        def fade_on():
            period = int(request.query.seconds)
            light_manager.fade_on(period)
            return {'success': True}

        @app.post('/fade-off')
        def fade_off():
            period = int(request.query.seconds)
            light_manager.fade_off(period)
            return {'success': True}

        @app.get('/status')
        def get_status():
            state = light_manager.state.state
            level = light_manager.light_controller.get_level()
            return {
                'state': state,
                'level': level,
            }

        run(app, host='0.0.0.0', port=8080)
