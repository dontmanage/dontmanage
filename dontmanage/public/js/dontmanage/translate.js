// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

// for translation
dontmanage._ = function (txt, replace, context = null) {
	if (!txt) return txt;
	if (typeof txt != "string") return txt;

	let translated_text = "";

	let key = txt; // txt.replace(/\n/g, "");
	if (context) {
		translated_text = dontmanage._messages[`${key}:${context}`];
	}

	if (!translated_text) {
		translated_text = dontmanage._messages[key] || txt;
	}

	if (replace && typeof replace === "object") {
		translated_text = $.format(translated_text, replace);
	}
	return translated_text;
};

window.__ = dontmanage._;

dontmanage.get_languages = function () {
	if (!dontmanage.languages) {
		dontmanage.languages = [];
		$.each(dontmanage.boot.lang_dict, function (lang, value) {
			dontmanage.languages.push({ label: lang, value: value });
		});
		dontmanage.languages = dontmanage.languages.sort(function (a, b) {
			return a.value < b.value ? -1 : 1;
		});
	}
	return dontmanage.languages;
};
