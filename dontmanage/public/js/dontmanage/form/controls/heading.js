dontmanage.ui.form.ControlHeading = class ControlHeading extends dontmanage.ui.form.ControlHTML {
	get_content() {
		return "<h4>" + __(this.df.label) + "</h4>";
	}
};
