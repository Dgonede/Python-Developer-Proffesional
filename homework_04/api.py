#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import re
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class CharField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class ArgumentsField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class EmailField(CharField):
    def __init__(self, required=False, nullable=False):
        super().__init__(required, nullable)


class PhoneField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class DateField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class BirthDayField(DateField):
    def __init__(self, required=False, nullable=False):
        super().__init__(required, nullable)


class GenderField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class ClientIDsField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class ClientsInterestsRequest(object):
    def __init__(self, client_ids, date=None):
        self.client_ids = client_ids
        self.date = date


class OnlineScoreRequest(object):
    def __init__(self, first_name=None, last_name=None, email=None, phone=None, birthday=None, gender=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.birthday = birthday
        self.gender = gender


class MethodRequest(object):
    def __init__(self, account=None, login=None, token=None, arguments=None, method=None):
        self.account = account
        self.login = login
        self.token = token
        self.arguments = arguments
        self.method = method

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    body = request.get("body", {})
    method = body.get("method")
    arguments = body.get("arguments", {})

    if "account" not in body or "login" not in body or "token" not in body:
        return "Authentication credentials missing", INVALID_REQUEST

    is_authenticated = check_auth(MethodRequest(
        account=body.get("account"),
        login=body.get("login"),
        token=body.get("token")
    ))

    if not is_authenticated:
        return "Forbidden: invalid credentials", FORBIDDEN

    if method == "online_score":
        return handle_online_score(arguments, ctx)

    elif method == "clients_interests":
        return handle_clients_interests(arguments, ctx)

    return "Method not found", INVALID_REQUEST


def handle_online_score(arguments, ctx):
    required_fields = ['phone', 'email']

    
    missing_fields = [field for field in required_fields if field not in arguments]
    if missing_fields:
        logging.warning(f"Missing required fields: {missing_fields}")
        return "Missing required fields", INVALID_REQUEST

    if not validate_email(arguments['email']):
        logging.warning(f"Invalid email format: {arguments['email']}")
        return "Invalid email format", INVALID_REQUEST

    # Проверка на формат телефонного номера
    phone = str(arguments.get('phone', '')).strip()  # получаем телефон
    if len(phone) == 11 and phone[0] in {'7', '8'}:  # Если начинается с '7' или '8'
        phone = phone[1:]  # Убираем код страны
    if not phone or not re.match(r'^\d{10}$', phone):  # проверяем 10 цифр
        logging.warning(f"Invalid phone number format: {arguments['phone']}")
        return "Phone must be a string of 10 digits.", INVALID_REQUEST

    # Проверяем на gender
    if 'gender' in arguments:
        try:
            gender = int(arguments['gender'])
            if gender not in GENDERS:
                logging.warning(f"Invalid gender value: {gender}")
                return "Invalid gender value", INVALID_REQUEST 
        except ValueError:
            logging.warning(f"Gender value is not an integer: {arguments['gender']}")
            return "Gender must be an integer", INVALID_REQUEST

    # Проверка на first_name и last_name
    for field in ['first_name', 'last_name']:
        if field in arguments and not isinstance(arguments[field], str):
            logging.warning(f"{field.replace('_', ' ').capitalize()} must be a string: {arguments[field]}")
            return f"{field.replace('_', ' ').capitalize()} must be a string", INVALID_REQUEST

    # Проверка на birthday
    if 'birthday' in arguments:
        try:
            datetime.datetime.strptime(arguments['birthday'], "%d.%m.%Y")  # Проверка формата даты
        except ValueError:
            logging.warning(f"Invalid birthday format: {arguments['birthday']}")
            return "Invalid birthday format. Use DD.MM.YYYY.", INVALID_REQUEST

    ctx["has"] = arguments
    score = 42

    # Если присутствует gender, добавляем к счёту
    if 'gender' in arguments and arguments['gender'] in GENDERS:
        score += 10

    if ctx.get("account") == ADMIN_LOGIN:
        return {"score": score}, OK

    return {"score": score}, OK


def handle_clients_interests(arguments, ctx):
    client_ids = arguments.get("client_ids")

    if not isinstance(client_ids, list) or not client_ids:
        return "Invalid client_ids format", INVALID_REQUEST
    
    if not all(isinstance(x, int) for x in client_ids):
        return "Invalid client_ids format", INVALID_REQUEST

    # Проверка на дату
    if "date" in arguments:
        if not isinstance(arguments["date"], str):
            return "Invalid date format. Expected string.", INVALID_REQUEST

        # Проверка формата даты
        try:
            datetime.datetime.strptime(arguments["date"], "%d.%m.%Y")
        except ValueError:
            return "Invalid date format. Use DD.MM.YYYY.", INVALID_REQUEST

    ctx["nclients"] = len(client_ids)
    ctx["has"] = arguments

    interests = {client_id: [f"interest_{client_id}_1", f"interest_{client_id}_2"] for client_id in client_ids}

    return interests, OK


def validate_email(email):
    # проверка формата email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()