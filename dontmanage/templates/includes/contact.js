// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.ready(function() {

	if(dontmanage.utils.get_url_arg('subject')) {
	  $('[name="subject"]').val(dontmanage.utils.get_url_arg('subject'));
	}

	$('.btn-send').off("click").on("click", function() {
		var email = $('[name="email"]').val();
		var message = $('[name="message"]').val();

		if(!(email && message)) {
			dontmanage.msgprint('{{ _("Please enter both your email and message so that we can get back to you. Thanks!") }}');
			return false;
		}

		if(!validate_email(email)) {
			dontmanage.msgprint('{{ _("You seem to have written your name instead of your email. Please enter a valid email address so that we can get back.") }}');
			$('[name="email"]').focus();
			return false;
		}

		$("#contact-alert").toggle(false);
		dontmanage.send_message({
			subject: $('[name="subject"]').val(),
			sender: email,
			message: message,
			callback: function(r) {
				if(r.message==="okay") {
					dontmanage.msgprint('{{ _("Thank you for your message") }}');
				} else {
					dontmanage.msgprint('{{ _("There were errors") }}');
					console.log(r.exc);
				}
				$(':input').val('');
			}
		}, this);
		return false;
	});

});

var msgprint = function(txt) {
	if(txt) $("#contact-alert").html(txt).toggle(true);
}
