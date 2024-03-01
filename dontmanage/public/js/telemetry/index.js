import "../lib/posthog.js";

class TelemetryManager {
	constructor() {
		this.enabled = false;

		this.project_id = dontmanage.boot.posthog_project_id;
		this.telemetry_host = dontmanage.boot.posthog_host;
		this.site_age = dontmanage.boot.telemetry_site_age;
		if (cint(dontmanage.boot.enable_telemetry) && this.project_id && this.telemetry_host) {
			this.enabled = true;
		}
	}

	initialize() {
		if (!this.enabled) return;
		let disable_decide = !this.should_record_session();
		try {
			posthog.init(this.project_id, {
				api_host: this.telemetry_host,
				autocapture: false,
				capture_pageview: false,
				capture_pageleave: false,
				advanced_disable_decide: disable_decide,
			});
			posthog.identify(dontmanage.boot.sitename);
			this.send_heartbeat();
			this.register_pageview_handler();
		} catch (e) {
			console.trace("Failed to initialize telemetry", e);
			this.enabled = false;
		}
	}

	capture(event, app, props) {
		if (!this.enabled) return;
		posthog.capture(`${app}_${event}`, props);
	}

	disable() {
		this.enabled = false;
	}

	can_enable() {
		if (cint(navigator.doNotTrack)) {
			return false;
		}
		let posthog_available = Boolean(this.telemetry_host && this.project_id);
		let sentry_available = Boolean(dontmanage.boot.sentry_dsn);
		return posthog_available || sentry_available;
	}

	send_heartbeat() {
		const KEY = "ph_last_heartbeat";
		const now = dontmanage.datetime.system_datetime(true);
		const last = localStorage.getItem(KEY);

		if (!last || moment(now).diff(moment(last), "hours") > 12) {
			localStorage.setItem(KEY, now.toISOString());
			this.capture("heartbeat", "dontmanage", { dontmanage_version: dontmanage.boot?.versions?.dontmanage });
		}
	}

	register_pageview_handler() {
		if (this.site_age && this.site_age > 6) {
			return;
		}

		dontmanage.router.on("change", () => {
			posthog.capture("$pageview");
		});
	}

	should_record_session() {
		let start = dontmanage.boot.sysdefaults.session_recording_start;
		if (!start) return;

		let start_datetime = dontmanage.datetime.str_to_obj(start);
		let now = dontmanage.datetime.now_datetime();
		// if user allowed recording only record for first 2 hours, never again.
		return dontmanage.datetime.get_minute_diff(now, start_datetime) < 120;
	}
}

dontmanage.telemetry = new TelemetryManager();
dontmanage.telemetry.initialize();
