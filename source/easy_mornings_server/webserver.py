from bottle import Bottle, run, request, abort
from .scheduler import Scheduler, ScheduledItem, CONSTANT_MODE


class WebServer:

    def __init__(self, scheduler: Scheduler):
        app = Bottle()

        @app.post('/on')
        def on():
            name = request.query.name or 'manual on'
            mode = request.query.mode or CONSTANT_MODE
            start_time = request.query.start_time or None
            if start_time is not None:
                start_time = int(start_time)
            end_time = request.query.end_time or None
            if end_time is not None:
                end_time = int(end_time)
            repeat = request.query.repeat or None
            days_of_week = request.query.repeat or None
            if days_of_week is not None:
                days_of_week = days_of_week.split(',')

            item = ScheduledItem(name=name,
                                 mode=mode,
                                 start_time=start_time,
                                 end_time=end_time,
                                 repeat=repeat,
                                 days_of_week=days_of_week,
                                 )

            scheduler.set_manual_override(item)
            return {'success': True}

        @app.post('/off')
        def off():
            scheduler.clear_manual_override()
            return {'success': True}

        @app.get('/schedule')
        def get_schedule():
            return {'schedule': scheduler.get_schedule_dicts()}

        @app.post('/schedule')
        def schedule():
            name = request.query.name
            if len(name) == 0:
                abort(400, 'name is empty')
            mode = request.query.mode
            if len(mode) == 0:
                abort(400, 'mode is empty')
            start_time = request.query.start_time
            if len(start_time) == 0:
                abort(400, 'start_time is empty')
            try:
                start_time = int(start_time)
            except ValueError:
                abort(400, 'start_time is not an integer')
            end_time = request.query.end_time
            if len(end_time) == 0:
                abort(400, 'end_time is empty')
            try:
                end_time = int(end_time)
            except ValueError:
                abort(400, 'end_time is not an integer')
            repeat = request.query.repeat
            if repeat.lower() == 'true':
                repeat = True
            else:
                repeat = False
            days_of_week = request.query.days_of_week or None
            if days_of_week is not None:
                days_of_week = days_of_week.split(',')

            item = ScheduledItem(name=name,
                                 mode=mode,
                                 start_time=start_time,
                                 end_time=end_time,
                                 repeat=repeat,
                                 days_of_week=days_of_week,
                                 )
            scheduler.add_item(item)
            return {'success': True}

        @app.delete('/schedule')
        def remove_item():
            name = request.query.name
            if len(name) == 0:
                abort(400, 'name is empty')
            found = scheduler.remove_item(name)
            return {'success': found}

        @app.post('/dismiss')
        def dismiss():
            scheduler.dismiss_active()
            return {'success': True}

        @app.get('/status')
        def get_status():
            current = scheduler.manual_override or scheduler.active
            return {'current': str(current)}

        run(app, host='localhost', port=8080)
