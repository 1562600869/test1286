import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            self.serve_file('index.html', 'text/html; charset=utf-8')
            return

        if path == '/api/courses':
            self.json_response(database.list_courses())
            return

        if path.startswith('/api/courses/') and path.endswith('/families'):
            course_id = int(path.split('/')[3])
            self.json_response(database.get_registration_families(course_id))
            return

        if path.startswith('/api/courses/'):
            course_id = int(path.split('/')[3])
            course = database.get_course(course_id)
            if course:
                self.json_response(course)
            else:
                self.error_response(404, '课程不存在')
            return

        if path == '/api/families':
            self.json_response(database.list_families())
            return

        if path.startswith('/api/families/'):
            family_id = int(path.split('/')[3])
            family = database.get_family(family_id)
            if family:
                self.json_response(family)
            else:
                self.error_response(404, '家庭不存在')
            return

        if path == '/api/registrations':
            course_id = params.get('course_id', [None])[0]
            family_id = params.get('family_id', [None])[0]
            if course_id:
                course_id = int(course_id)
            if family_id:
                family_id = int(family_id)
            self.json_response(database.list_registrations(course_id, family_id))
            return

        if path == '/api/attendances':
            course_id = params.get('course_id', [None])[0]
            family_id = params.get('family_id', [None])[0]
            attendance_date = params.get('attendance_date', [None])[0]
            if course_id:
                course_id = int(course_id)
            if family_id:
                family_id = int(family_id)
            self.json_response(database.list_attendances(course_id, family_id, attendance_date))
            return

        if path == '/api/stats/monthly':
            year = params.get('year', [None])[0]
            month = params.get('month', [None])[0]
            if year:
                year = int(year)
            if month:
                month = int(month)
            self.json_response(database.get_monthly_stats(year, month))
            return

        self.error_response(404, '路径不存在')

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        data = self.read_json_body()

        try:
            if path == '/api/courses':
                result = database.add_course(
                    name=data['name'],
                    course_type=data['course_type'],
                    age_group=data['age_group'],
                    fee=int(data['fee']),
                    max_students=int(data['max_students']),
                    status=data.get('status', '开放报名')
                )
                self.json_response(result, 201)
                return

            if path == '/api/families':
                result = database.add_family(
                    parent_name=data['parent_name'],
                    parent_phone=data['parent_phone'],
                    child_name=data['child_name'],
                    child_age=int(data['child_age'])
                )
                self.json_response(result, 201)
                return

            if path == '/api/registrations':
                result = database.register_course(
                    course_id=int(data['course_id']),
                    family_id=int(data['family_id'])
                )
                self.json_response(result, 201)
                return

            if path == '/api/attendances':
                result = database.add_attendance(
                    course_id=int(data['course_id']),
                    family_id=int(data['family_id']),
                    attendance_date=data.get('attendance_date')
                )
                self.json_response(result, 201)
                return

            self.error_response(404, '路径不存在')
        except ValueError as e:
            self.error_response(400, str(e))
        except KeyError as e:
            self.error_response(400, f'缺少必填字段: {e}')

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        data = self.read_json_body()

        try:
            if path.startswith('/api/courses/'):
                course_id = int(path.split('/')[3])
                result = database.update_course(
                    course_id=course_id,
                    name=data['name'],
                    course_type=data['course_type'],
                    age_group=data['age_group'],
                    fee=int(data['fee']),
                    max_students=int(data['max_students']),
                    status=data['status']
                )
                if result:
                    self.json_response(result)
                else:
                    self.error_response(404, '课程不存在')
                return

            if path.startswith('/api/families/'):
                family_id = int(path.split('/')[3])
                result = database.update_family(
                    family_id=family_id,
                    parent_name=data['parent_name'],
                    parent_phone=data['parent_phone'],
                    child_name=data['child_name'],
                    child_age=int(data['child_age'])
                )
                if result:
                    self.json_response(result)
                else:
                    self.error_response(404, '家庭不存在')
                return

            self.error_response(404, '路径不存在')
        except ValueError as e:
            self.error_response(400, str(e))
        except KeyError as e:
            self.error_response(400, f'缺少必填字段: {e}')

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/courses/'):
            course_id = int(path.split('/')[3])
            if database.delete_course(course_id):
                self.json_response({'success': True})
            else:
                self.error_response(404, '课程不存在')
            return

        if path.startswith('/api/families/'):
            family_id = int(path.split('/')[3])
            if database.delete_family(family_id):
                self.json_response({'success': True})
            else:
                self.error_response(404, '家庭不存在')
            return

        self.error_response(404, '路径不存在')

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode('utf-8')
        return json.loads(body)

    def serve_file(self, filename, content_type):
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            self.error_response(404, '文件不存在')
            return
        with open(filepath, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def error_response(self, status, message):
        body = json.dumps({'error': message}, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f'[{self.address_string()}] {format % args}')


def main():
    database.init_db()
    port = 6193
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'科技馆课程管理系统已启动: http://localhost:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')
        server.server_close()


if __name__ == '__main__':
    main()
