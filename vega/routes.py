from flask import render_template, request, redirect, url_for, flash, session, make_response
import json
import websocket
from websocket import create_connection
from vega import app
from datetime import datetime, timezone
import tzlocal
from .forms import LoginForm, CreateUserForm, AddDeviceForm


URL_WS = "ws://localhost:8002/"


success_result_add_device_list = [
    "added",
    "updated",
    "nothingToUpdate",
    "updateViaMacBuffer"
]


def send_req(req: dict) -> dict:
    ws = create_connection(url=URL_WS)
    if req.get("cmd") != "auth_req":
        recovery_session = {"cmd": "token_auth_req", 'token': session.get('token')}
        ws.send(json.dumps(recovery_session))
        resp_json = json.loads(ws.recv())
        if resp_json.get('cmd') == "console":
            ws.recv()
        if resp_json.get("status"):
            session['token'] = resp_json.get('token')
        print("==========================")
        print(f"|command - {req.get('cmd')}|")
        print(resp_json)
        print("==========================")
    print("sended")
    ws.send(json.dumps(req))  # Get command
    print("recieved")
    resp_json = json.loads(ws.recv())
    if resp_json.get('cmd') == "console":
        ws.recv()
        return send_req(req)
    print("==========================")
    print(f"|command - {req.get('cmd')}|")
    print(resp_json)
    print("==========================")
    ws.close()
    return resp_json


@app.route("/delete_device/<string:dev_eui>", methods=["GET"])
def delete_device(dev_eui):
    if session.get('token') is None:
        redirect(url_for('login'))
    device_list = list()
    device_list.append(dev_eui)
    query = {
        "cmd": "delete_devices_req",
        "devices_list": device_list
    }
    print(f"query - {query}")
    resp = send_req(query)
    if resp.get("status") and resp.get("device_delete_status")[0].get('status') == 'deleted':
        flash("Device was deleted", "info")
    else:
        flash(f"Device was not deleted, because '{resp.get('err_string')}'", "error")
    return redirect(url_for('index'))


@app.route("/delete_user/<string:login>", methods=["GET"])
def delete_user(login):
    if session.get('token') is None:
        redirect(url_for('login'))
    user_list = list()
    user_list.append(login)
    query = {
        "cmd": "delete_users_req",
        "user_list": user_list
    }
    print(f"query - {query}")
    resp = send_req(query)
    if resp.get("status") and resp.get("delete_user_list")[0].get('status') and resp.get("err_string") is None:
        flash("user was deleted", "info")
    else:
        flash(f"User was not deleted, because '{resp.get('err_string')}'", "error")
    return redirect(url_for('index'))


@app.route('/dev_graph/<string:dev_eui>/<int:limit>', methods=["GET"])
def dev_chart(dev_eui, limit):
    if session.get('token') is None:
        redirect(url_for('login'))
    context = dict()
    title = f"Chart of {dev_eui}"
    context["legend"] = dev_eui
    query_req = {
        "cmd": "get_data_req",
        "devEui": dev_eui,
        "select":
            {
                "limit": limit
            }
    }
    resp = send_req(query_req)
    if not resp.get("status"):
        flash(resp.get("err_string"), 'error')
        return render_template("index.html")
    if resp.get("cmd") == "get_data_resp":
        data_list = resp.get("data_list")
        labels = list()
        data = list()
        for every_data in data_list:
            # labels.append(datetime.fromtimestamp(every_data.get('ts'), timezone.utc))
            every_data['ts'] = str(datetime.fromtimestamp(every_data.get('ts')/1000, timezone.utc))
            labels.append(every_data.get('ts'))
            data.append(every_data.get('data'))
        context["data"] = data
        context["labels"] = labels
        context["raw_data_list"] = data_list
        context["raw_data_list_keys"] = data_list[0].keys()
        return render_template("chart.html", context=context, title=title)


@app.route('/create_user/', methods=['post', 'get'])
def create_user():
    context = dict()
    form = CreateUserForm()
    if request.method == "POST":
        form.devEui_list.choices = form.devEui_list.data
    if form.validate_on_submit():
        login = form.login.data  # запрос к данным формы
        password = form.password.data
        login = form.login.data
        password = form.password.data
        device_access = form.device_access.data
        console_enable = form.console_enable.data
        devEui_list = form.devEui_list.data
        command_list = form.command_list.data
        unsolicited = form.unsolicited.data
        direction = form.direction.data
        with_MAC_Commands = form.with_MAC_Commands.data

        set_data = {
            "login": login,
            "password": password,
            "device_access": device_access,
            "consoleEnable": console_enable,
            "devEui_list": devEui_list,
            "command_list": command_list,
            "rx_settings": {
                "unsolicited": unsolicited,
                "direction": direction,
                "withMacCommands": with_MAC_Commands
            }
        }
        user_list = list()
        user_list.append(set_data)
        query = {
            "cmd": "manage_users_req",
            "user_list": user_list
        }
        resp = send_req(query)
        if resp.get("err_string") is None:
            return redirect(url_for('index'))
        else:
            flash(resp.get("err_string"), 'error')
        return render_template('create_user.html', form=form, context=context)
    query = {
        "cmd": "get_devices_req"
    }
    resp = send_req(query)
    devices_list = resp.get("devices_list")
    form.devEui_list.data = [dev.get("devName") for dev in devices_list]
    dev_Euis = [dev.get("devEui") for dev in devices_list]
    dev_names = [dev.get("devName") for dev in devices_list]
    form.command_list.choices = session.get('command_list')
    form.devEui_list.choices = dev_Euis
    return render_template('create_user.html', form=form, context=context)


@app.route('/add_device/', methods=['post', 'get'])
def add_device():
    context = dict()
    form = AddDeviceForm()
    if request.method == "POST":
        if form.is_submitted():
            dev_eui = form.dev_eui.data  # запрос к данным формы
            dev_name = form.dev_name.data
            dev_address = form.dev_address.data
            apps_key = form.apps_key.data
            nwks_key = form.nwks_key.data
            app_eui = form.app_eui.data
            app_key = form.app_key.data
            set_data = {
                "devEui": dev_eui,
            }
            if dev_address is not None and apps_key != "" and nwks_key is not None:
                abp = {
                    "devAddress": dev_address,
                    "appsKey": apps_key,
                    "mwksKey": nwks_key
                }
                set_data["ABP"] = abp
            if app_key != "":
                otaa = {
                    "appKey": app_key,
                }
                if app_eui != "":
                    otaa["appEui"] = app_eui
                set_data["OTAA"] = otaa

            if dev_name is not None:
                set_data["devName"] = dev_name

            device_list = list()
            device_list.append(set_data)
            query = {
                "cmd": "manage_devices_req",
                "devices_list": device_list
            }
            print(f'query add dev - {query}')
            resp = send_req(query)
            if resp.get("err_string") is None and resp.get('device_add_status')[0].get("status") in success_result_add_device_list:
                return redirect(url_for('index'))
            else:
                flash(resp.get('device_add_status')[0].get("status"), 'error')
            return render_template('add_device.html', form=form, context=context)
    return render_template('add_device.html', form=form, context=context)


@app.route('/')
def index():
    context = dict()
    if 'token' not in session:
        return redirect('login')
    # Get information from connected server
    srvinfo = {"cmd": "server_info_req"}  # Don't change!

    # Get device list w/attributes
    devalist = {"cmd": "get_device_appdata_req"}  # Don't change!

    # Get reg users
    reguser = {"cmd": "get_users_req"}  # Don't change!
    infresp_dict = send_req(srvinfo)
    if infresp_dict.get("err_string") == "unknown_auth":
        return redirect(url_for('login'))
    if "manage_users" in session.get("command_list"):
        context['is_can_create_user'] = True
    if "manage_devices" in session.get("command_list"):
        context['is_can_add_device'] = True
    if "delete_users" in session.get("command_list"):
        context['is_can_delete_user'] = True
    if "delete_devices" in session.get("command_list"):
        context['is_can_delete_device'] = True
    time_serv_now = infresp_dict.get("time").get("utc") / 1000
    local_timezone = tzlocal.get_localzone()
    serv_time = datetime.fromtimestamp(time_serv_now, local_timezone)
    context['time'] = serv_time.strftime("%Y-%m-%d %H:%M:%S")
    context['city'] = infresp_dict.get("time").get("time_zone", 'None')
    # Get dev list w/attributes
    devalistresp = send_req(devalist)
    context["devices_list"] = devalistresp.get("devices_list")

    # Get registered users
    reguserresponse = send_req(reguser)
    context["user_list"] = reguserresponse.get("user_list")
    return render_template('index.html', context=context)


@app.route('/logout/')
def logout():
    if 'token' in session:
        log_out = {"cmd": "close_auth_req",  # Don't change!
                   "token": session.get("token")
                   }
        out = send_req(log_out)
        if out.get("err_string") is None:
            flash("You have been logged out.")
            session.pop('token', None)
            return redirect(url_for('login'))
    return redirect(url_for('login'))


@app.route('/login/', methods=['post', 'get'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login = form.login.data # запрос к данным формы
        password = form.password.data

        # Autorization on VEGA server
        autreq = {"cmd": "auth_req",  # Don't change!
                  "login": str(login),  # Login name
                  "password": str(password)  # password
                  }
        autresp = send_req(autreq)
        if autresp.get("err_string") is None:
            session["command_list"] = autresp.get("command_list")
            session['token'] = autresp.get("token")
            return redirect(url_for('index'))
        else:
            flash("Invalid login/password", 'error')
    return render_template('login.html', form=form)
