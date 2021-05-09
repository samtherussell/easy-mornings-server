from bottle import Bottle, run, request
from .lightmanager import LightManager


class WebServer:

    def __init__(self, light_manager: LightManager):
        app = Bottle()

        @app.post('/now')
        def set_now():
            level = request.query.level
            level = float(level) if level else None
            light_manager.set_level(level)
            return {'success': True}

        @app.post('/fade')
        def fade():
            level = request.query.level
            level = float(level) if level else None
            period = int(request.query.seconds)
            light_manager.fade(period, level)
            return {'success': True}

        @app.post('/timer')
        def timer():
            level = request.query.level
            level = float(level) if level else None
            period = int(request.query.seconds)
            light_manager.timer(period, level)
            return {'success': True}

        @app.get('/status')
        def get_status():
            state = light_manager.state.state
            level = light_manager.level
            return {
                'state': state,
                'level': level,
            }

        run(app, host='0.0.0.0', port=8080)
