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


class CharField:
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if self.required and not value:
            raise ValueError("This field is required.")


class EmailField(CharField):
    def validate(self, value):
        super().validate(value)
        if value and not self.validate_email(value):
            raise ValueError(f"Invalid email format: {value}")

    @staticmethod
    def validate_email(email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None


class PhoneField(CharField):
    def validate(self, value):
        super().validate(value)
        if value:
            phone = str(value).strip()
            if len(phone) == 11 and phone[0] == '7':
                return
            elif len(phone) == 10:
                phone = '7' + phone
            else:
                raise ValueError(f"Phone must be a string of 11 digits starting with 7. Provided: {value}")
            if not re.match(r'^\d{11}$', phone):
                raise ValueError(f"Phone must be a string of 11 digits starting with 7. Provided: {value}")


class BirthDayField(CharField):
    def validate(self, value):
        super().validate(value)
        if value:
            try:
                datetime.datetime.strptime(value, "%d.%m.%Y")
            except ValueError:
                raise ValueError(f"Invalid birthday format: {value}")


class GenderField(CharField):
    def validate(self, value):
        super().validate(value)
        if value:
            try:
                gender = int(value)
                if gender not in GENDERS:
                    raise ValueError(f"Invalid gender value: {gender}")
            except ValueError:
                raise ValueError(f"Gender must be an integer: {value}")


class OnlineScoreRequest:
    def __init__(self, first_name=None, last_name=None, email=None, phone=None, birthday=None, gender=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.birthday = birthday
        self.gender = gender
        self.errors = {}

    def validate(self):
        email_field = EmailField(required=True)
        phone_field = PhoneField(required=True)
        birthday_field = BirthDayField(required=False)
        gender_field = GenderField(required=False)

        # Валидация каждого из полей
        try:
            email_field.validate(self.email)
        except ValueError as e:
            self.errors['email'] = str(e)

        try:
            phone_field.validate(self.phone)
        except ValueError as e:
            self.errors['phone'] = str(e)

        if self.birthday:
            try:
                birthday_field.validate(self.birthday)
            except ValueError as e:
                self.errors['birthday'] = str(e)

        if self.gender is not None:
            try:
                gender_field.validate(self.gender)
            except ValueError as e:
                self.errors['gender'] = str(e)

        if self.errors:
            raise ValueError(self.errors)

    @property
    def email_value(self):
        return self.email

    @property
    def phone_value(self):
        return self.phone

    @property
    def birthday_value(self):
        return self.birthday

    @property
    def gender_value(self):
        return self.gender


class MethodRequest:
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
    request = OnlineScoreRequest(
        first_name=arguments.get('first_name'),
        last_name=arguments.get('last_name'),
        email=arguments.get('email'),
        phone=arguments.get('phone'),
        birthday=arguments.get('birthday'),
        gender=arguments.get('gender')
    )

    try:
        request.validate()
    except ValueError as e:
        logging.warning(f"Validation errors: {e.args[0]}")
        return e.args[0], INVALID_REQUEST

    ctx["has"] = arguments
    score = 42
    return {"score": score}, OK


def handle_clients_interests(arguments, ctx):
    client_ids = arguments.get("client_ids")

    if not isinstance(client_ids, list) or not client_ids:
        return "Invalid client_ids format", INVALID_REQUEST
    
    if not all(isinstance(x, int) for x in client_ids):
        return "Invalid client_ids format", INVALID_REQUEST

    
    if "date" in arguments:
        if not isinstance(arguments["date"], str):
            return "Invalid date format. Expected string.", INVALID_REQUEST

        
        try:
            datetime.datetime.strptime(arguments["date"], "%d.%m.%Y")
        except ValueError:
            return "Invalid date format. Use DD.MM.YYYY.", INVALID_REQUEST

    ctx["nclients"] = len(client_ids)
    ctx["has"] = arguments

    interests = {client_id: [f"interest_{client_id}_1", f"interest_{client_id}_2"] for client_id in client_ids}

    return interests, OK


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
        r = {"response": response, "code": code} if code not in ERRORS else {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
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