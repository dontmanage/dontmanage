# Copyright (c) 2017, DontManage and Contributors
# License: MIT. See LICENSE
import os
from base64 import b32encode, b64encode
from io import BytesIO

import pyotp
from pyqrcode import create as qrcreate

import dontmanage
import dontmanage.defaults
from dontmanage import _
from dontmanage.utils import cint, get_datetime, get_url, time_diff_in_seconds
from dontmanage.utils.background_jobs import enqueue
from dontmanage.utils.password import decrypt, encrypt

PARENT_FOR_DEFAULTS = "__2fa"


def get_default(key):
	return dontmanage.db.get_default(key, parent=PARENT_FOR_DEFAULTS)


def set_default(key, value):
	dontmanage.db.set_default(key, value, parent=PARENT_FOR_DEFAULTS)


def clear_default(key):
	dontmanage.defaults.clear_default(key, parent=PARENT_FOR_DEFAULTS)


class ExpiredLoginException(Exception):
	pass


def toggle_two_factor_auth(state, roles=None):
	"""Enable or disable 2FA in site_config and roles"""
	for role in roles or []:
		role = dontmanage.get_doc("Role", {"role_name": role})
		role.two_factor_auth = cint(state)
		role.save(ignore_permissions=True)


def two_factor_is_enabled(user=None):
	"""Returns True if 2FA is enabled."""
	enabled = int(dontmanage.db.get_single_value("System Settings", "enable_two_factor_auth") or 0)
	if enabled:
		bypass_two_factor_auth = int(
			dontmanage.db.get_single_value("System Settings", "bypass_2fa_for_retricted_ip_users") or 0
		)
		if bypass_two_factor_auth and user:
			user_doc = dontmanage.get_doc("User", user)
			restrict_ip_list = (
				user_doc.get_restricted_ip_list()
			)  # can be None or one or more than one ip address
			if restrict_ip_list and dontmanage.local.request_ip:
				for ip in restrict_ip_list:
					if dontmanage.local.request_ip.startswith(ip):
						enabled = False
						break

	if not user or not enabled:
		return enabled
	return two_factor_is_enabled_for_(user)


def should_run_2fa(user):
	"""Check if 2fa should run."""
	return two_factor_is_enabled(user=user)


def get_cached_user_pass():
	"""Get user and password if set."""
	user = pwd = None
	tmp_id = dontmanage.form_dict.get("tmp_id")
	if tmp_id:
		user = dontmanage.safe_decode(dontmanage.cache().get(tmp_id + "_usr"))
		pwd = dontmanage.safe_decode(dontmanage.cache().get(tmp_id + "_pwd"))
	return (user, pwd)


def authenticate_for_2factor(user):
	"""Authenticate two factor for enabled user before login."""
	if dontmanage.form_dict.get("otp"):
		return
	otp_secret = get_otpsecret_for_(user)
	token = int(pyotp.TOTP(otp_secret).now())
	tmp_id = dontmanage.generate_hash(length=8)
	cache_2fa_data(user, token, otp_secret, tmp_id)
	verification_obj = get_verification_obj(user, token, otp_secret)
	# Save data in local
	dontmanage.local.response["verification"] = verification_obj
	dontmanage.local.response["tmp_id"] = tmp_id


def cache_2fa_data(user, token, otp_secret, tmp_id):
	"""Cache and set expiry for data."""
	pwd = dontmanage.form_dict.get("pwd")
	verification_method = get_verification_method()

	# set increased expiry time for SMS and Email
	if verification_method in ["SMS", "Email"]:
		expiry_time = dontmanage.flags.token_expiry or 300
		dontmanage.cache().set(tmp_id + "_token", token)
		dontmanage.cache().expire(tmp_id + "_token", expiry_time)
	else:
		expiry_time = dontmanage.flags.otp_expiry or 180
	for k, v in {"_usr": user, "_pwd": pwd, "_otp_secret": otp_secret}.items():
		dontmanage.cache().set(f"{tmp_id}{k}", v)
		dontmanage.cache().expire(f"{tmp_id}{k}", expiry_time)


def two_factor_is_enabled_for_(user):
	"""Check if 2factor is enabled for user."""
	if user == "Administrator":
		return False

	if isinstance(user, str):
		user = dontmanage.get_doc("User", user)

	roles = [d.role for d in user.roles or []] + ["All"]

	role_doctype = dontmanage.qb.DocType("Role")
	no_of_users = dontmanage.db.count(
		role_doctype,
		filters=((role_doctype.two_factor_auth == 1) & (role_doctype.name.isin(roles))),
	)

	if int(no_of_users) > 0:
		return True

	return False


def get_otpsecret_for_(user):
	"""Set OTP Secret for user even if not set."""
	if otp_secret := get_default(user + "_otpsecret"):
		return decrypt(otp_secret)

	otp_secret = b32encode(os.urandom(10)).decode("utf-8")
	set_default(user + "_otpsecret", encrypt(otp_secret))
	dontmanage.db.commit()

	return otp_secret


def get_verification_method():
	return dontmanage.db.get_single_value("System Settings", "two_factor_method")


def confirm_otp_token(login_manager, otp=None, tmp_id=None):
	"""Confirm otp matches."""
	from dontmanage.auth import get_login_attempt_tracker

	if not otp:
		otp = dontmanage.form_dict.get("otp")
	if not otp:
		if two_factor_is_enabled_for_(login_manager.user):
			return False
		return True
	if not tmp_id:
		tmp_id = dontmanage.form_dict.get("tmp_id")
	hotp_token = dontmanage.cache().get(tmp_id + "_token")
	otp_secret = dontmanage.cache().get(tmp_id + "_otp_secret")
	if not otp_secret:
		raise ExpiredLoginException(_("Login session expired, refresh page to retry"))

	tracker = get_login_attempt_tracker(login_manager.user)

	hotp = pyotp.HOTP(otp_secret)
	if hotp_token:
		if hotp.verify(otp, int(hotp_token)):
			dontmanage.cache().delete(tmp_id + "_token")
			tracker.add_success_attempt()
			return True
		else:
			tracker.add_failure_attempt()
			login_manager.fail(_("Incorrect Verification code"), login_manager.user)

	totp = pyotp.TOTP(otp_secret)
	if totp.verify(otp):
		# show qr code only once
		if not get_default(login_manager.user + "_otplogin"):
			set_default(login_manager.user + "_otplogin", 1)
			delete_qrimage(login_manager.user)
		tracker.add_success_attempt()
		return True
	else:
		tracker.add_failure_attempt()
		login_manager.fail(_("Incorrect Verification code"), login_manager.user)


def get_verification_obj(user, token, otp_secret):
	otp_issuer = dontmanage.db.get_single_value("System Settings", "otp_issuer_name")
	verification_method = get_verification_method()
	verification_obj = None
	if verification_method == "SMS":
		verification_obj = process_2fa_for_sms(user, token, otp_secret)
	elif verification_method == "OTP App":
		# check if this if the first time that the user is trying to login. If so, send an email
		if not get_default(user + "_otplogin"):
			verification_obj = process_2fa_for_email(user, token, otp_secret, otp_issuer, method="OTP App")
		else:
			verification_obj = process_2fa_for_otp_app(user, otp_secret, otp_issuer)
	elif verification_method == "Email":
		verification_obj = process_2fa_for_email(user, token, otp_secret, otp_issuer)
	return verification_obj


def process_2fa_for_sms(user, token, otp_secret):
	"""Process sms method for 2fa."""
	phone = dontmanage.db.get_value("User", user, ["phone", "mobile_no"], as_dict=1)
	phone = phone.mobile_no or phone.phone
	status = send_token_via_sms(otp_secret, token=token, phone_no=phone)
	verification_obj = {
		"token_delivery": status,
		"prompt": status
		and "Enter verification code sent to {}".format(phone[:4] + "******" + phone[-3:]),
		"method": "SMS",
		"setup": status,
	}
	return verification_obj


def process_2fa_for_otp_app(user, otp_secret, otp_issuer):
	"""Process OTP App method for 2fa."""
	totp_uri = pyotp.TOTP(otp_secret).provisioning_uri(user, issuer_name=otp_issuer)
	if get_default(user + "_otplogin"):
		otp_setup_completed = True
	else:
		otp_setup_completed = False

	verification_obj = {"method": "OTP App", "setup": otp_setup_completed}
	return verification_obj


def process_2fa_for_email(user, token, otp_secret, otp_issuer, method="Email"):
	"""Process Email method for 2fa."""
	subject = None
	message = None
	status = True
	prompt = ""
	if method == "OTP App" and not get_default(user + "_otplogin"):
		"""Sending one-time email for OTP App"""
		totp_uri = pyotp.TOTP(otp_secret).provisioning_uri(user, issuer_name=otp_issuer)
		qrcode_link = get_link_for_qrcode(user, totp_uri)
		message = get_email_body_for_qr_code({"qrcode_link": qrcode_link})
		subject = get_email_subject_for_qr_code({"qrcode_link": qrcode_link})
		prompt = _(
			"Please check your registered email address for instructions on how to proceed. Do not close this window as you will have to return to it."
		)
	else:
		"""Sending email verification"""
		prompt = _("Verification code has been sent to your registered email address.")
	status = send_token_via_email(
		user, token, otp_secret, otp_issuer, subject=subject, message=message
	)
	verification_obj = {
		"token_delivery": status,
		"prompt": status and prompt,
		"method": "Email",
		"setup": status,
	}
	return verification_obj


def get_email_subject_for_2fa(kwargs_dict):
	"""Get email subject for 2fa."""
	subject_template = _("Login Verification Code from {}").format(
		dontmanage.db.get_single_value("System Settings", "otp_issuer_name")
	)
	subject = dontmanage.render_template(subject_template, kwargs_dict)
	return subject


def get_email_body_for_2fa(kwargs_dict):
	"""Get email body for 2fa."""
	body_template = """
		Enter this code to complete your login:
		<br><br>
		<b style="font-size: 18px;">{{ otp }}</b>
	"""
	body = dontmanage.render_template(body_template, kwargs_dict)
	return body


def get_email_subject_for_qr_code(kwargs_dict):
	"""Get QRCode email subject."""
	subject_template = _("One Time Password (OTP) Registration Code from {}").format(
		dontmanage.db.get_single_value("System Settings", "otp_issuer_name")
	)
	subject = dontmanage.render_template(subject_template, kwargs_dict)
	return subject


def get_email_body_for_qr_code(kwargs_dict):
	"""Get QRCode email body."""
	body_template = _(
		"Please click on the following link and follow the instructions on the page. {0}"
	).format("<br><br> <a href='{{qrcode_link}}'>{{qrcode_link}}</a>")
	body = dontmanage.render_template(body_template, kwargs_dict)
	return body


def get_link_for_qrcode(user, totp_uri):
	"""Get link to temporary page showing QRCode."""
	key = dontmanage.generate_hash(length=20)
	key_user = f"{key}_user"
	key_uri = f"{key}_uri"
	lifespan = int(dontmanage.db.get_single_value("System Settings", "lifespan_qrcode_image")) or 240
	dontmanage.cache().set_value(key_uri, totp_uri, expires_in_sec=lifespan)
	dontmanage.cache().set_value(key_user, user, expires_in_sec=lifespan)
	return get_url(f"/qrcode?k={key}")


def send_token_via_sms(otpsecret, token=None, phone_no=None):
	"""Send token as sms to user."""
	try:
		from dontmanage.core.doctype.sms_settings.sms_settings import send_request
	except Exception:
		return False

	if not phone_no:
		return False

	ss = dontmanage.get_doc("SMS Settings", "SMS Settings")
	if not ss.sms_gateway_url:
		return False

	hotp = pyotp.HOTP(otpsecret)
	args = {ss.message_parameter: f"Your verification code is {hotp.at(int(token))}"}

	for d in ss.get("parameters"):
		args[d.parameter] = d.value

	args[ss.receiver_parameter] = phone_no

	sms_args = {"params": args, "gateway_url": ss.sms_gateway_url, "use_post": ss.use_post}
	enqueue(
		method=send_request,
		queue="short",
		timeout=300,
		event=None,
		is_async=True,
		job_name=None,
		now=False,
		**sms_args,
	)
	return True


def send_token_via_email(user, token, otp_secret, otp_issuer, subject=None, message=None):
	"""Send token to user as email."""
	user_email = dontmanage.db.get_value("User", user, "email")
	if not user_email:
		return False
	hotp = pyotp.HOTP(otp_secret)
	otp = hotp.at(int(token))
	template_args = {"otp": otp, "otp_issuer": otp_issuer}
	if not subject:
		subject = get_email_subject_for_2fa(template_args)
	if not message:
		message = get_email_body_for_2fa(template_args)

	email_args = {
		"recipients": user_email,
		"sender": None,
		"subject": subject,
		"message": message,
		"header": [_("Verfication Code"), "blue"],
		"delayed": False,
		"retry": 3,
	}

	enqueue(
		method=dontmanage.sendmail,
		queue="short",
		timeout=300,
		event=None,
		is_async=True,
		job_name=None,
		now=False,
		**email_args,
	)
	return True


def get_qr_svg_code(totp_uri):
	"""Get SVG code to display Qrcode for OTP."""
	url = qrcreate(totp_uri)
	svg = ""
	stream = BytesIO()
	try:
		url.svg(stream, scale=4, background="#eee", module_color="#222")
		svg = stream.getvalue().decode().replace("\n", "")
		svg = b64encode(svg.encode())
	finally:
		stream.close()
	return svg


def qrcode_as_png(user, totp_uri):
	"""Save temporary Qrcode to server."""
	folder = create_barcode_folder()
	png_file_name = f"{dontmanage.generate_hash(length=20)}.png"
	_file = dontmanage.get_doc(
		{
			"doctype": "File",
			"file_name": png_file_name,
			"attached_to_doctype": "User",
			"attached_to_name": user,
			"folder": folder,
			"content": png_file_name,
		}
	)
	_file.save()
	dontmanage.db.commit()
	file_url = get_url(_file.file_url)
	file_path = os.path.join(dontmanage.get_site_path("public", "files"), _file.file_name)
	url = qrcreate(totp_uri)
	with open(file_path, "w") as png_file:
		url.png(png_file, scale=8, module_color=[0, 0, 0, 180], background=[0xFF, 0xFF, 0xCC])
	return file_url


def create_barcode_folder():
	"""Get Barcodes folder."""
	folder_name = "Barcodes"
	folder = dontmanage.db.exists("File", {"file_name": folder_name})
	if folder:
		return folder
	folder = dontmanage.get_doc(
		{"doctype": "File", "file_name": folder_name, "is_folder": 1, "folder": "Home"}
	)
	folder.insert(ignore_permissions=True)
	return folder.name


def delete_qrimage(user, check_expiry=False):
	"""Delete Qrimage when user logs in."""
	user_barcodes = dontmanage.get_all(
		"File", {"attached_to_doctype": "User", "attached_to_name": user, "folder": "Home/Barcodes"}
	)

	for barcode in user_barcodes:
		if check_expiry and not should_remove_barcode_image(barcode):
			continue
		barcode = dontmanage.get_doc("File", barcode.name)
		dontmanage.delete_doc("File", barcode.name, ignore_permissions=True)


def delete_all_barcodes_for_users():
	"""Task to delete all barcodes for user."""

	users = dontmanage.get_all("User", {"enabled": 1})
	for user in users:
		if not two_factor_is_enabled(user=user.name):
			continue
		delete_qrimage(user.name, check_expiry=True)


def should_remove_barcode_image(barcode):
	"""Check if it's time to delete barcode image from server."""
	if isinstance(barcode, str):
		barcode = dontmanage.get_doc("File", barcode)
	lifespan = dontmanage.db.get_single_value("System Settings", "lifespan_qrcode_image") or 240
	if time_diff_in_seconds(get_datetime(), barcode.creation) > int(lifespan):
		return True
	return False


def disable():
	dontmanage.db.set_single_value("System Settings", "enable_two_factor_auth", 0)


@dontmanage.whitelist()
def reset_otp_secret(user):
	if dontmanage.session.user != user:
		dontmanage.only_for("System Manager", message=True)

	otp_issuer = dontmanage.db.get_single_value("System Settings", "otp_issuer_name")
	user_email = dontmanage.db.get_value("User", user, "email")

	clear_default(user + "_otplogin")
	clear_default(user + "_otpsecret")

	email_args = {
		"recipients": user_email,
		"sender": None,
		"subject": _("OTP Secret Reset - {0}").format(otp_issuer or "DontManage Framework"),
		"message": _(
			"<p>Your OTP secret on {0} has been reset. If you did not perform this reset and did not request it, please contact your System Administrator immediately.</p>"
		).format(otp_issuer or "DontManage Framework"),
		"delayed": False,
		"retry": 3,
	}

	enqueue(
		method=dontmanage.sendmail,
		queue="short",
		timeout=300,
		event=None,
		is_async=True,
		job_name=None,
		now=False,
		**email_args,
	)

	dontmanage.msgprint(_("OTP Secret has been reset. Re-registration will be required on next login."))
