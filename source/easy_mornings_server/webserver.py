from bottle import Bottle, run, request
from .lightmanager import LightManager
import json

class WebServer:

    def __init__(self, light_manager: LightManager):
        app = Bottle()

        @app.post('/now')
        def now():
            level = float(request.query.level)
            light_manager.constant(level)
            return {'success': True}

        @app.post('/fade')
        def fade():
            level = float(request.query.level)
            period = int(request.query.seconds)
            light_manager.fade(period, level)
            return {'success': True}

        @app.post('/timer')
        def timer():
            level = float(request.query.level)
            period = int(request.query.seconds)
            light_manager.timer(period, level)
            return {'success': True}

        @app.post('/rave')
        def timer():
            light_manager.rave()
            return {'success': True}

        @app.get('/status')
        def get_status():
            return light_manager.status()

        @app.post('/schedule')
        def add_schedule_item():
            values = json.load(request.body)
            item_id = light_manager.schedule.add(values)
            return {'success': True, 'id': item_id}

        @app.get('/schedule')
        def get_schedule():
            item = light_manager.schedule.getall()
            return {'success': True, 'items': item}

        @app.get('/schedule/<item_id>')
        def get_schedule_item(item_id):
            item = light_manager.schedule.get(item_id)
            return {'success': True, 'item': item}

        @app.delete('/schedule/<item_id>')
        def get_schedule_item(item_id):
            light_manager.schedule.remove(item_id)
            return {'success': True}

        run(app, host='0.0.0.0', port=8080)
