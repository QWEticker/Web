import wtforms
from flask_wtf import FlaskForm
from wtforms.validators import Length, InputRequired, NumberRange, ValidationError

all_command_list = [
    "get_users",
    "manage_users",
    "delete_users",
    "get_device_appdata",
    "get_data",
    "send_data",
    "manage_device_appdata",
    "delete_device_appdata",
    "get_gateways",
    "manage_gateways",
    "delete_gateways",
    "get_devices",
    "manage_devices",
    "delete_devices",
    "get_coverage_map",
    "get_device_downlink_queue",
    "manage_device_downlink_queue",
    "server_info",
    "send_email",
    "tx"
]


class LoginForm(FlaskForm):
    login = wtforms.StringField("Логин: ", validators=[InputRequired()])
    password = wtforms.PasswordField("Пароль: ", validators=[InputRequired(), Length(min=1, max=100)])
    submit = wtforms.SubmitField("Войти")


class CreateUserForm(FlaskForm):
    login = wtforms.StringField("Логин: ", validators=[InputRequired()])
    password = wtforms.PasswordField("Пароль: ", validators=[])
    device_access = wtforms.SelectField("Доступ к устройству: ", choices=["FULL", "SELECTED"], default="SELECTED")
    console_enable = wtforms.BooleanField("Работа с консолью")
    devEui_list = wtforms.SelectMultipleField("DevEui список")
    command_list = wtforms.SelectMultipleField("Список команд", choices=all_command_list)
    unsolicited = wtforms.BooleanField("Unsolicited")
    direction = wtforms.SelectField("Направление", choices=["UPLINK", "DOWNLINK", "ALL"])
    with_MAC_Commands = wtforms.BooleanField("С MAC коммандами")
    submit = wtforms.SubmitField("Внести")


def is_string_is_hex(form, field):
    for ch in field.data:
        if ((ch < '0' or ch > '9') and
                (ch < 'A' or ch > 'F')):
            raise ValidationError('Field must be in HEX')


class AddDeviceForm(FlaskForm):
    dev_eui = wtforms.StringField("EUI устройства*: ",
                                  validators=[InputRequired(), is_string_is_hex,
                                              Length(16, 16, message="Must be 16 length")])
    dev_name = wtforms.StringField("Имя устройства: ")
    dev_address = wtforms.IntegerField(
        "Адрес устройства: ",
        validators=[NumberRange(min=0x00000001, max=0xFFFFFFFF, message="0x00000001 and 0xFFFFFFFF desired")])
    apps_key = wtforms.StringField("Application session key: ",
                                   validators=[Length(32, 32, message="Must be 32 length"), is_string_is_hex], default="")
    nwks_key = wtforms.StringField("Network session key: ",
                                   validators=[Length(32, 32, message="Must be 32 length"), is_string_is_hex],
                                   default="")
    app_eui = wtforms.StringField("Application EUI: ",
                                  validators=[Length(16, 16, message="Must be 16 length"), is_string_is_hex],
                                  default="")
    app_key = wtforms.StringField("Application key: ",
                                  validators=[Length(32, 32, message="Must be 32 length"), is_string_is_hex],
                                  default="")
    class_user = wtforms.SelectField("Класс пользователя", choices=['CLASS_A', 'CLASS_C'])
    submit = wtforms.SubmitField("Добавить")
