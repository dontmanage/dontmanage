import * as Sentry from "@sentry/browser";

Sentry.init({
	dsn: dontmanage.boot.sentry_dsn,
	release: dontmanage?.boot?.versions?.dontmanage,
	autoSessionTracking: false,
	initialScope: {
		// don't use dontmanage.session.user, it's set much later and will fail because of async loading
		user: { id: dontmanage.boot.sitename },
		tags: { dontmanage_user: dontmanage.boot.user.name ?? "Unidentified" },
	},
	beforeSend(event, hint) {
		// Check if it was caused by dontmanage.throw()
		if (
			hint.originalException instanceof Error &&
			hint.originalException.stack &&
			hint.originalException.stack.includes("dontmanage.throw")
		) {
			return null;
		}
		return event;
	},
});
