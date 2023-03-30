dontmanage.pages["user-profile"].on_page_load = function (wrapper) {
	dontmanage.require("user_profile_controller.bundle.js", () => {
		let user_profile = new dontmanage.ui.UserProfile(wrapper);
		user_profile.show();
	});
};
