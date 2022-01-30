import datetime
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin


class SessionDeadMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if not request.user.is_superuser:
            try:
                res = request.session.get('last_action')
                res1 = datetime.datetime.strptime(res, '%Y-%m-%dT%H:%M:%S.%f')
                delta = (datetime.datetime.now() - res1).seconds
                if delta > 60:
                    logout(request)
            except TypeError or AttributeError:
                request.session['last_action'] = datetime.datetime.now().isoformat()
            request.session['last_action'] = datetime.datetime.now().isoformat()
        else:
            pass
