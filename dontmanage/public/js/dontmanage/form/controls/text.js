dontmanage.ui.form.ControlText = class ControlText extends dontmanage.ui.form.ControlData {
	static html_element = "textarea";
	static horizontal = false;
	make_wrapper() {
		super.make_wrapper();
		this.$wrapper.find(".like-disabled-input").addClass("for-description");
	}
	make_input() {
		super.make_input();
		this.$input.css({ height: "300px" });
		if (this.df.max_height) {
			this.$input.css({ "max-height": this.df.max_height });
		}
	}
};

dontmanage.ui.form.ControlLongText = dontmanage.ui.form.ControlText;
dontmanage.ui.form.ControlSmallText = class ControlSmallText extends dontmanage.ui.form.ControlText {
	make_input() {
		super.make_input();
		this.$input.css({ height: "150px" });
	}
};
