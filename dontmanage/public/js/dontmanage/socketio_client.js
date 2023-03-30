import { io } from "socket.io-client";
dontmanage.socketio = {
	open_tasks: {},
	open_docs: [],
	emit_queue: [],

	init: function (port = 3000) {
		if (dontmanage.boot.disable_async) {
			return;
		}

		if (dontmanage.socketio.socket) {
			return;
		}

		// Enable secure option when using HTTPS
		if (window.location.protocol == "https:") {
			dontmanage.socketio.socket = io.connect(dontmanage.socketio.get_host(port), {
				secure: true,
				withCredentials: true,
				reconnectionAttempts: 3,
			});
		} else if (window.location.protocol == "http:") {
			dontmanage.socketio.socket = io.connect(dontmanage.socketio.get_host(port), {
				withCredentials: true,
				reconnectionAttempts: 3,
			});
		}

		if (!dontmanage.socketio.socket) {
			console.log("Unable to connect to " + dontmanage.socketio.get_host(port));
			return;
		}

		dontmanage.socketio.socket.on("msgprint", function (message) {
			dontmanage.msgprint(message);
		});

		dontmanage.socketio.socket.on("progress", function (data) {
			if (data.progress) {
				data.percent = (flt(data.progress[0]) / data.progress[1]) * 100;
			}
			if (data.percent) {
				dontmanage.show_progress(
					data.title || __("Progress"),
					data.percent,
					100,
					data.description,
					true
				);
			}
		});

		dontmanage.socketio.setup_listeners();
		dontmanage.socketio.setup_reconnect();

		$(document).on("form-load form-rename", function (e, frm) {
			if (!frm.doc || frm.is_new()) {
				return;
			}

			for (var i = 0, l = dontmanage.socketio.open_docs.length; i < l; i++) {
				var d = dontmanage.socketio.open_docs[i];
				if (frm.doctype == d.doctype && frm.docname == d.name) {
					// already subscribed
					return false;
				}
			}

			dontmanage.socketio.doc_subscribe(frm.doctype, frm.docname);
		});

		$(document).on("form-refresh", function (e, frm) {
			if (!frm.doc || frm.is_new()) {
				return;
			}

			dontmanage.socketio.doc_open(frm.doctype, frm.docname);
		});

		$(document).on("form-unload", function (e, frm) {
			if (!frm.doc || frm.is_new()) {
				return;
			}

			// dontmanage.socketio.doc_unsubscribe(frm.doctype, frm.docname);
			dontmanage.socketio.doc_close(frm.doctype, frm.docname);
		});

		$(document).on("form-typing", function (e, frm) {
			dontmanage.socketio.form_typing(frm.doctype, frm.docname);
		});

		$(document).on("form-stopped-typing", function (e, frm) {
			dontmanage.socketio.form_stopped_typing(frm.doctype, frm.docname);
		});

		window.addEventListener("beforeunload", () => {
			if (!cur_frm || !cur_frm.doc || cur_frm.is_new()) {
				return;
			}

			dontmanage.socketio.doc_close(cur_frm.doctype, cur_frm.docname);
		});
	},
	get_host: function (port = 3000) {
		var host = window.location.origin;
		if (window.dev_server) {
			var parts = host.split(":");
			port = dontmanage.boot.socketio_port || port.toString() || "3000";
			if (parts.length > 2) {
				host = parts[0] + ":" + parts[1];
			}
			host = host + ":" + port;
		}
		return host;
	},
	subscribe: function (task_id, opts) {
		// TODO DEPRECATE

		dontmanage.socketio.socket.emit("task_subscribe", task_id);
		dontmanage.socketio.socket.emit("progress_subscribe", task_id);

		dontmanage.socketio.open_tasks[task_id] = opts;
	},
	task_subscribe: function (task_id) {
		dontmanage.socketio.socket.emit("task_subscribe", task_id);
	},
	task_unsubscribe: function (task_id) {
		dontmanage.socketio.socket.emit("task_unsubscribe", task_id);
	},
	doctype_subscribe: function (doctype) {
		dontmanage.socketio.socket.emit("doctype_subscribe", doctype);
	},
	doc_subscribe: function (doctype, docname) {
		if (dontmanage.flags.doc_subscribe) {
			console.log("throttled");
			return;
		}

		dontmanage.flags.doc_subscribe = true;

		// throttle to 1 per sec
		setTimeout(function () {
			dontmanage.flags.doc_subscribe = false;
		}, 1000);

		dontmanage.socketio.socket.emit("doc_subscribe", doctype, docname);
		dontmanage.socketio.open_docs.push({ doctype: doctype, docname: docname });
	},
	doc_unsubscribe: function (doctype, docname) {
		dontmanage.socketio.socket.emit("doc_unsubscribe", doctype, docname);
		dontmanage.socketio.open_docs = $.filter(dontmanage.socketio.open_docs, function (d) {
			if (d.doctype === doctype && d.name === docname) {
				return null;
			} else {
				return d;
			}
		});
	},
	doc_open: function (doctype, docname) {
		// notify that the user has opened this doc, if not already notified
		if (
			!dontmanage.socketio.last_doc ||
			dontmanage.socketio.last_doc[0] != doctype ||
			dontmanage.socketio.last_doc[1] != docname
		) {
			dontmanage.socketio.socket.emit("doc_open", doctype, docname);

			dontmanage.socketio.last_doc &&
				dontmanage.socketio.doc_close(
					dontmanage.socketio.last_doc[0],
					dontmanage.socketio.last_doc[1]
				);
		}
		dontmanage.socketio.last_doc = [doctype, docname];
	},
	doc_close: function (doctype, docname) {
		// notify that the user has closed this doc
		dontmanage.socketio.socket.emit("doc_close", doctype, docname);

		// if the doc is closed the user has also stopped typing
		dontmanage.socketio.socket.emit("doc_typing_stopped", doctype, docname);
	},
	form_typing: function (doctype, docname) {
		// notifiy that the user is typing on the doc
		dontmanage.socketio.socket.emit("doc_typing", doctype, docname);
	},
	form_stopped_typing: function (doctype, docname) {
		// notifiy that the user has stopped typing
		dontmanage.socketio.socket.emit("doc_typing_stopped", doctype, docname);
	},
	setup_listeners: function () {
		dontmanage.socketio.socket.on("task_status_change", function (data) {
			dontmanage.socketio.process_response(data, data.status.toLowerCase());
		});
		dontmanage.socketio.socket.on("task_progress", function (data) {
			dontmanage.socketio.process_response(data, "progress");
		});
	},
	setup_reconnect: function () {
		// subscribe again to open_tasks
		dontmanage.socketio.socket.on("connect", function () {
			// wait for 5 seconds before subscribing again
			// because it takes more time to start python server than nodejs server
			// and we use validation requests to python server for subscribing
			setTimeout(function () {
				$.each(dontmanage.socketio.open_tasks, function (task_id, opts) {
					dontmanage.socketio.subscribe(task_id, opts);
				});

				// re-connect open docs
				$.each(dontmanage.socketio.open_docs, function (d) {
					if (locals[d.doctype] && locals[d.doctype][d.name]) {
						dontmanage.socketio.doc_subscribe(d.doctype, d.name);
					}
				});

				if (cur_frm && cur_frm.doc && !cur_frm.is_new()) {
					dontmanage.socketio.doc_open(cur_frm.doc.doctype, cur_frm.doc.name);
				}
			}, 5000);
		});
	},
	process_response: function (data, method) {
		if (!data) {
			return;
		}

		// success
		var opts = dontmanage.socketio.open_tasks[data.task_id];
		if (opts[method]) {
			opts[method](data);
		}

		// "callback" is std dontmanage term
		if (method === "success") {
			if (opts.callback) opts.callback(data);
		}

		// always
		dontmanage.request.cleanup(opts, data);
		if (opts.always) {
			opts.always(data);
		}

		// error
		if (data.status_code && data.status_code > 400 && opts.error) {
			opts.error(data);
		}
	},
};

dontmanage.provide("dontmanage.realtime");
dontmanage.realtime.on = function (event, callback) {
	dontmanage.socketio.socket && dontmanage.socketio.socket.on(event, callback);
};

dontmanage.realtime.off = function (event, callback) {
	dontmanage.socketio.socket && dontmanage.socketio.socket.off(event, callback);
};

dontmanage.realtime.publish = function (event, message) {
	if (dontmanage.socketio.socket) {
		dontmanage.socketio.socket.emit(event, message);
	}
};
